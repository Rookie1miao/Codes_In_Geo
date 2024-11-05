import os
import numpy as np
import rasterio
from multiprocessing import Pool, cpu_count
import numpy as np
import rasterio
import pymannkendall as mk
import os
# 输入和输出文件夹路径

input_folder = 'tiles'           # 存放原始多波段小块的文件夹
mk_output_folder = 'mk_tiles'    # 存放MK检验结果的小块文件夹
sen_output_folder = 'sen_tiles'  # 存放Sen's斜率结果的小块文件夹

# 创建输出文件夹（如果不存在）
os.makedirs(mk_output_folder, exist_ok=True)
os.makedirs(sen_output_folder, exist_ok=True)

# 获取所有小块文件列表
tile_files = [f for f in os.listdir(input_folder) if f.endswith('.tif')]

def process_tile(tile_file):


    input_tile_path = os.path.join(input_folder, tile_file)
    
    # 构建输出文件名
    base_name = os.path.splitext(tile_file)[0]  # 去掉文件扩展名
    # 生成对应的MK和Sen's斜率文件名
    mk_tile_file = 'mk' + base_name[4:] + '.tif'   # 去掉前缀，加上'mk'
    sen_tile_file = 'sen' + base_name[4:] + '.tif'
    mk_tile_path = os.path.join(mk_output_folder, mk_tile_file)
    sen_tile_path = os.path.join(sen_output_folder, sen_tile_file)
    
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
        
        # 创建时间序列索引（假设为等间隔时间）
        time = np.arange(bands)
        
        # 将数据重塑为二维数组，形状为 (pixels, bands)
        data_reshaped = data.reshape(bands, -1).T  # (pixels, bands)
        
        # 创建掩膜数组
        mask = data_reshaped == nodata_value
        masked_data = np.ma.array(data_reshaped, mask=mask)
        
        # 预先分配结果数组
        num_pixels = data_reshaped.shape[0]
        mk_result = np.full(num_pixels, nodata_value, dtype=np.float32)
        sen_result = np.full(num_pixels, nodata_value, dtype=np.float32)
        
        # 遍历所有像素
        for idx in range(num_pixels):
            pixel_series = masked_data[idx]
            valid_data = pixel_series.compressed()  # 获取有效值
                
            if len(valid_data) < 2:
                continue  # 无法进行趋势分析，结果保持为 nodata_value
            else:
                # 使用 pymannkendall 进行 MK 检验和 Sen's 斜率估计
                result = mk.original_test(valid_data)
                mk_result[idx] = result.z  # MK检验的Z值
                sen_result[idx] = result.slope  # Sen's斜率
                
        # 将结果重塑回二维数组，形状为 (rows, cols)
        mk_result_2d = mk_result.reshape(rows, cols)
        sen_result_2d = sen_result.reshape(rows, cols)
        
        # 更新输出文件的元数据
        profile.update(dtype=rasterio.float32, count=1, nodata=nodata_value)
        
        # 写入MK检验结果
        with rasterio.open(mk_tile_path, 'w', **profile) as dst_mk:
            dst_mk.write(mk_result_2d, 1)
        
        # 写入Sen's斜率结果
        with rasterio.open(sen_tile_path, 'w', **profile) as dst_sen:
            dst_sen.write(sen_result_2d, 1)
        
        # 清理内存
        del data
        del masked_data
        del mk_result
        del sen_result

    print(f"处理完成：{tile_file}")

if __name__ == '__main__':
    num_workers = cpu_count()
    print(f"使用 {num_workers} 个工作进程进行并行处理。")

    with Pool(processes=num_workers) as pool:
        pool.map(process_tile, tile_files)

    print("所有小块的MK趋势检验和Sen's斜率估计已完成并保存到对应的文件夹中。")
