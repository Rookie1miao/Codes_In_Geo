import os
import numpy as np
import rasterio
from multiprocessing import Pool, cpu_count
#from pycpt import pettitt
P_VALUE = 0.05

input_folder = 'tiles'               # 存放原始多波段小块的文件夹
pettitt_output_folder = 'pettitt_tiles'  # 存放Pettitt检验结果的小块文件夹

os.makedirs(pettitt_output_folder, exist_ok=True)

# 获取所有小块文件列表
tile_files = [f for f in os.listdir(input_folder) if f.endswith('.tif')]

def pettitt(x):
    n = len(x)
    k = np.arange(1, n + 1)
    U = np.zeros(n)
    for t in range(n):
        s1 = np.sum(np.sign(x[t] - x[:t]))
        s2 = np.sum(np.sign(x[t+1:] - x[t]))
        U[t] = s1 + s2
    K = np.argmax(np.abs(U))
    Umax = U[K]
    p_value = 2 * np.exp((-6 * Umax**2) / (n**3 + n**2))
    return K, p_value

def process_tile(tile_file):
    input_tile_path = os.path.join(input_folder, tile_file)
    
    # 构建输出文件名
    base_name = os.path.splitext(tile_file)[0]  # 去掉文件扩展名
    # 生成对应的Pettitt检验结果文件名
    pettitt_tile_file = 'pettitt' + base_name[4:] + '.tif'   # 去掉前缀，加上'pettitt'
    pettitt_tile_path = os.path.join(pettitt_output_folder, pettitt_tile_file)
    
    # 打开小块文件
    with rasterio.open(input_tile_path) as src:
        data = src.read()  # 数据形状为 (bands, rows, cols)
        profile = src.profile
        
        # 获取数据维度
        bands, rows, cols = data.shape
        
        # 获取 nodata 值
        nodata_value = -9999
        if src.nodata is not None:
            nodata_value = src.nodata
        
        # 将数据重塑为二维数组，形状为 (pixels, bands)
        data_reshaped = data.reshape(bands, -1).T  # (pixels, bands)
        
        # 创建掩膜数组
        masked_data = np.ma.masked_equal(data_reshaped, nodata_value)
        
        # 预先分配结果数组
        num_pixels = data_reshaped.shape[0]
        pettitt_result = np.full(num_pixels, nodata_value, dtype=np.float32)
        
        # 遍历所有像素
        for idx in range(num_pixels):
            pixel_series = masked_data[idx]    # 当前像素的时间序列，掩膜数组
            valid_data = pixel_series.compressed()  # 获取有效值（已排除 nodata_value）
            
            # 如果有效数据点少于一定数量，无法进行突变点检测
            if len(valid_data) < 5:
                pettitt_result[idx] = nodata_value
                continue
            else:
                K, p_value = pettitt(valid_data)
                if p_value < P_VALUE:
                    # 检测到显著的突变点，记录突变点的位置
                    pettitt_result[idx] = K + 1  # 转换为1-based索引
                else:
                    # 未检测到显著的突变点
                    pettitt_result[idx] = 0
                        
        # 将结果重塑回二维数组，形状为 (rows, cols)
        pettitt_result_2d = pettitt_result.reshape(rows, cols)
        
        # 更新输出文件的元数据
        profile.update(dtype=rasterio.float32, count=1, nodata=nodata_value)
        
        # 写入 Pettitt 检验结果
        with rasterio.open(pettitt_tile_path, 'w', **profile) as dst_pettitt:
            dst_pettitt.write(pettitt_result_2d, 1)
        
        # 清理内存
        del data
        del data_reshaped
        del masked_data
        del pettitt_result

    print(f"处理完成：{tile_file}")

if __name__ == '__main__':
    num_workers = cpu_count()
    print(f"使用 {num_workers} 个工作进程进行并行处理。")

    with Pool(processes=num_workers) as pool:
        pool.map(process_tile, tile_files)

    print("所有小块的 Pettitt 突变检测已完成并保存到对应的文件夹中。")
