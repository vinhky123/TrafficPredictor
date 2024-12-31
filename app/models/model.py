import torch
import math
import torch.nn as nn
import os

base_dir = os.getcwd()
model_state_path = os.path.join(base_dir, "notebook/TimeXer.pth")


class PositionalEmbedding(nn.Module):
    def __init__(self, d_model, max_len=5000):
        super(PositionalEmbedding, self).__init__()
        # Compute the positional encodings once in log space.
        pe = torch.zeros(max_len, d_model).float()
        pe.requires_grad = False

        position = torch.arange(0, max_len).float().unsqueeze(1)
        div_term = (
            torch.arange(0, d_model, 2).float() * -(math.log(10000.0) / d_model)
        ).exp()

        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)

        pe = pe.unsqueeze(0)
        self.register_buffer("pe", pe)

    def forward(self, x):
        return self.pe[:, : x.size(1)]


class Inverted_EmbeddingData(nn.Module):
    def __init__(self, input_size, d_model, drop_out=0.1):
        super(Inverted_EmbeddingData, self).__init__()

        self.input_size = input_size
        self.projection = nn.Linear(self.input_size, d_model)
        self.dropout = nn.Dropout(drop_out)

    def forward(self, x):
        x = x.permute(0, 2, 1)
        return self.dropout(self.projection(x))


class EnEmbedding(nn.Module):
    def __init__(self, d_model, patch_len, drop_out=0.1, num_variate=2):
        super(EnEmbedding, self).__init__()

        self.n_vars = num_variate
        self.patch_len = patch_len

        self.value_embedding = nn.Linear(patch_len, d_model)
        self.glb_token = nn.Parameter(torch.randn(1, self.n_vars, 1, d_model))
        self.position_embedding = PositionalEmbedding(d_model)

        self.dropout = nn.Dropout(drop_out)

    def forward(self, x):
        # (B, num variate, seq_len)
        n_vars = x.shape[1]
        glb = self.glb_token.repeat((x.shape[0], 1, 1, 1))
        # Patching the sequence
        x = x.unfold(dimension=-1, size=self.patch_len, step=self.patch_len)

        x = torch.reshape(x, (x.shape[0] * x.shape[1], x.shape[2], x.shape[3]))
        x = self.value_embedding(x) + self.position_embedding(x)
        x = torch.reshape(x, (-1, n_vars, x.shape[-2], x.shape[-1]))
        # Concate global token to data
        x = torch.cat([x, glb], dim=2)
        x = torch.reshape(x, (x.shape[0] * x.shape[1], x.shape[2], x.shape[3]))

        return self.dropout(x), n_vars


class FlattenHead(nn.Module):
    def __init__(self, n_vars, nf, target_window, head_dropout=0.1):
        super().__init__()
        self.n_vars = n_vars
        self.flatten = nn.Flatten(start_dim=-2)
        self.linear = nn.Linear(nf, target_window)
        self.dropout = nn.Dropout(head_dropout)

    def forward(self, x):  # x: [bs, nvars, d_model, patch_num]
        x = self.flatten(x)  # x: [bs, nvars, d_model * patch_num]
        x = self.linear(x)
        x = self.dropout(x)
        return x


class Attention(nn.Module):
    def __init__(self, d_model, n_head=4, dropout=0.1):
        super(Attention, self).__init__()

        self.multihead_attn = nn.MultiheadAttention(
            embed_dim=d_model, num_heads=n_head, dropout=dropout
        )
        self.dropout = nn.Dropout(dropout)

    def forward(self, query, key, value, attn_mask=None):

        query = query.permute(1, 0, 2)  # (B, L, D) -> (L, B, D)
        key = key.permute(1, 0, 2)
        value = value.permute(1, 0, 2)

        attn_output, attn_weights = self.multihead_attn(
            query, key, value, attn_mask=attn_mask
        )
        attn_output = attn_output.permute(1, 0, 2)  # (L, B, D) -> (B, L, D)
        return self.dropout(attn_output)


class TX_EncoderLayer(nn.Module):
    def __init__(self, d_model):
        super(TX_EncoderLayer, self).__init__()
        self.self_attn = Attention(d_model)
        self.cross_attn = Attention(d_model)
        d_ff = d_model * 4

        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)
        self.norm3 = nn.LayerNorm(d_model)

        self.conv1 = nn.Conv1d(d_model, d_ff, kernel_size=1)
        self.conv2 = nn.Conv1d(d_ff, d_model, kernel_size=1)

        self.dropout = nn.Dropout(0.1)
        self.activation = nn.functional.gelu

    def forward(self, x, cross, attn_mask=None):
        B, L, D = cross.shape
        # Self-Attention
        attn = self.self_attn(x, x, x)
        # attn = self.self_attn(x, x, x, attn_mask=attn_mask)
        x = x + self.dropout(attn)
        x = self.norm1(x)

        # Cross-Attention with global token
        glb_token_ori = x[:, -1, :].unsqueeze(1)
        glb = torch.reshape(glb_token_ori, (B, -1, D))

        cross_attn = self.cross_attn(glb, cross, cross, attn_mask=attn_mask)
        cross_attn = torch.reshape(
            cross_attn, (cross_attn.shape[0] * cross_attn.shape[1], cross_attn.shape[2])
        ).unsqueeze(1)

        glb_token_ori = glb_token_ori + self.dropout(cross_attn)

        glb_token = self.norm2(glb_token_ori)
        y = torch.cat([x[:, :-1, :], glb_token], dim=1)

        # Feed-Forward Network
        y = self.dropout(self.activation(self.conv1(y.transpose(-1, 1))))
        y = self.dropout(self.conv2(y).transpose(-2, -1))

        return self.norm3(x + y)


class TX_Encoder(nn.Module):
    def __init__(self, d_model, num_layers):
        super(TX_Encoder, self).__init__()

        self.e_layers = nn.ModuleList(
            [TX_EncoderLayer(d_model) for _ in range(num_layers)]
        )
        self.norm = nn.LayerNorm(d_model)

    def forward(self, x, cross, attn_mask=None):
        # B, L, D
        for layer in self.e_layers:
            x = layer(x, cross, attn_mask=attn_mask)

        x = self.norm(x)
        return x


class TimeXer(nn.Module):
    def __init__(
        self,
        seq_len,
        patch_len,
        patch_num,
        num_variate,
        pred_len,
        use_norm=True,
        d_model=256,
        num_layers=4,
    ):
        super(TimeXer, self).__init__()

        self.use_norm = use_norm
        self.seq_len = seq_len
        self.pred_len = pred_len
        self.patch_len = patch_len
        self.patch_num = patch_num
        self.d_model = d_model
        self.num_variate = num_variate
        self.num_layers = num_layers

        self.en_embedding = EnEmbedding(
            self.d_model, self.patch_len, num_variate=self.num_variate
        )
        self.ex_embedding = Inverted_EmbeddingData(self.seq_len, self.d_model)

        self.encoder = TX_Encoder(self.d_model, self.num_layers)
        self.head_nf = self.d_model * (self.patch_num + 1)
        self.head = FlattenHead(self.num_variate, self.head_nf, self.pred_len)

    def forward(self, x, attn_mask=None):
        # (B, seq_len, num_variate)
        if self.use_norm:
            means = x.mean(1, keepdim=True).detach()
            x = x - means
            stdev = torch.sqrt(torch.var(x, dim=1, keepdim=True, unbiased=False) + 1e-5)
            x = x / stdev

        en_data = x.permute(0, 2, 1)
        ex_data = x

        en_embedded, n_vars = self.en_embedding(en_data)
        ex_embedded = self.ex_embedding(ex_data)

        encoder_out = self.encoder(en_embedded, ex_embedded, attn_mask=attn_mask)
        encoder_out = torch.reshape(
            encoder_out, (-1, n_vars, encoder_out.shape[-2], encoder_out.shape[-1])
        )
        encoder_out = encoder_out.permute(0, 1, 3, 2)

        output = self.head(encoder_out)
        output = output.permute(0, 2, 1)

        if self.use_norm:
            output = output * (stdev[:, 0, :].unsqueeze(1).repeat(1, self.pred_len, 1))
            output = output + (means[:, 0, :].unsqueeze(1).repeat(1, self.pred_len, 1))

        return output


class GetModel(object):
    def __init__(self):
        self.model = TimeXer(
            seq_len=96,
            patch_len=12,
            patch_num=8,
            num_variate=325,
            pred_len=12,
            use_norm=True,
            d_model=256,
            num_layers=4,
        )
        self.model.load_state_dict(torch.load(model_state_path, weights_only=True))
        self.model.eval()

    def predict(self, data):
        return self.model(data)
