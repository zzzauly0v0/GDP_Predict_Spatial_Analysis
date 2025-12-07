from torch import nn
import torch

class Seq2Seq(nn.Module):
    def __init__(self,input_size, hidden_size, num_layers, output_size, predict_steps):
        '''
        :param input_size: 输入特征的数量
        :param hidden_size: 隐藏层
        :param num_layers: LSTM堆叠层数
        :param output_size: 输出特征，即预测特征
        :param predict_steps:预测的年数
        '''
        super(Seq2Seq, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.output_size = output_size
        self.predict_steps = predict_steps

        self.encoder = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.decoder = nn.LSTM(output_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, output_size)

    def forward(self, x):
        # 得到整个历史序列的最终隐状态作为上下文向量 (hn, cn)
        # enc_hn, enc_cn 形状: (num_layers, B, H)
        # 1. 编码器阶段
        _, (enc_hn, enc_cn) = self.encoder(x)
        # 初始化结果容器，用来存储未来时间步的GDP预测值
        predictions = torch.zeros(x.size(0), self.predict_steps, self.output_size).to(x.device)
        # 初始化解码器的第一个输入（未来的数据全为0）
        dec_input = torch.zeros(x.size(0), 1, self.output_size).to(x.device)
        # 初始化解码器的隐藏状态 (继承自编码器)
        decoder_h = enc_hn
        decoder_c = enc_cn
        # 4. 迭代预测未来 P 个时间步
        for t in range(self.predict_steps):
            dec_output, (decoder_h, decoder_c) = self.decoder(
                dec_input,
                (decoder_h, decoder_c)
            )
            pred = self.fc(dec_output.squeeze(1))
            # 将预测的值存储到容器中
            predictions[:, t, :] = pred
            # 将当前的解码器重新增加一个时间步维度
            dec_input = pred.unsqueeze(1)

        return predictions
