library(corrplot) 
library(vegan) 
library(ggcor)
library(openxlsx)
library(ggplot2)
# 读取Excel文件
varespec <- read.xlsx("D:/print/PC1.xlsx", sheet = 1)

# 查看数据
print(varespec)
# 读取Excel文件
varechem <- read.xlsx("D:/print/性状1.xlsx", sheet = 1)

# 查看数据
print(varechem)

df03 <- fortify_cor(x = varechem, y = varespec)
ggcor(df03) + geom_colour()
mantel <- mantel_test(varespec, varechem,spec.select = list(shannon = 1:1, #依次定义四种物种作为Mantel的分析对象 
                                                            chao1 = 2:2, 
                                                            PC1 = 3:3, 
                                                            PC2 = 4:4)) %>%  
  mutate(rd = cut(r, breaks = c(-Inf, 0.2, 0.4, Inf), 
                  labels = c("< 0.2", "0.2 - 0.4", ">= 0.4")),#定义Mantel的R值范围标签，便于出图 
         pd = cut(p.value, breaks = c(-Inf, 0.01, 0.05, Inf), 
                  labels = c("< 0.01", "0.01 - 0.05", ">= 0.05")))#定义Mantel检验的p值范围标签，便于出图 
quickcor(varechem, type = "upper") +#绘制理化数据热图 
  geom_square() +#定义成方块状 
  anno_link(aes(colour = pd, size = rd), data = mantel) +#定义连线 
  scale_size_manual(values = c(0.5, 1, 2))+ 
  guides(size = guide_legend(title = "Mantel's r",#定义图例 
                             order = 2), 
         colour = guide_legend(title = "Mantel's p",  
                               order = 3), 
         fill = guide_colorbar(title = "Pearson's r", order = 4)) 
