library(ggplot2)
library(reshape2)
library(scales)
library(RColorBrewer)

data <- read.csv("D:/print/次表层属与桃产量品质相关性Heatmap图_相关性矩阵Correlation表.csv")

# 将数据从宽格式转换为长格式
data_long <- melt(data, id.vars = "name", variable.name = "Indicator", value.name = "Correlation")

# 计算圆的大小和标记
data_long$Size <- abs(data_long$Correlation) * 10
data_long$Stars <- ifelse(abs(data_long$Correlation) >= 0.526, "**",
                          ifelse(abs(data_long$Correlation) >= 0.413, "*", ""))
# 调整因子水平，确保因子顺序正确，避免排序引起的对齐问题
data_long$Indicator <- factor(data_long$Indicator, levels=unique(data_long$Indicator))
data_long$name <- factor(data_long$name, levels=rev(unique(data_long$name)))  # 反转name的顺序

# 绘图
custom_colors <- c("#67001F", "#B2182B", "#D6604D", "#F4A582", "#FFFFFF", "#92C5DE", "#4393C3", "#2166AC", "#053061")

# 绘图
gg <- ggplot(data_long, aes(x = Indicator, y = name)) +
  geom_tile(aes(width = 1, height = 1), fill = "white", color = "grey80") + # 指定tile的宽高为1
  geom_point(aes(size = Size, color = Correlation), position = position_identity(), alpha = 1,stroke = 1.3) + # 确保点的位置
  geom_text(aes(label = Stars), vjust = 0.5, hjust = 0.5, size = 3) + # 标记星号
  scale_size(range = c(3, 10), guide = FALSE) + # 点的大小范围，不显示图例
  scale_colour_gradientn(colours = custom_colors,  # 使用自定义颜色
                         values = rescale(c(-1, 0, 1)),
                         breaks = c(-1, 0, 1),
                         labels = c("-1", "0", "1"),
                         limits = c(-1, 1),
                         guide = guide_colourbar(title = "Correlation", barheight = unit(4, "cm"))) +
  theme_minimal() + 
  theme(
    panel.grid.major = element_blank(),
    panel.background = element_rect(fill = "white", color = NA),
    plot.background = element_rect(color = NA, fill = "white"),
    axis.line = element_blank(),
    axis.text.x = element_text(angle = 0, vjust = 0.4, hjust = 0.5),
    axis.text.y = element_text(hjust = 0), # 向右移动纵向标签
    axis.ticks = element_blank(),
    panel.spacing = unit(1.5, "lines")
  ) +
  scale_x_discrete(position = "top") +
  coord_fixed(ratio = 1) +
  labs(title = "Correlation between Indicators and Names", x = "Indicator", y = "Name")

print(gg)








