import os
import rasterio
from rasterio.windows import Window

# 输入大TIF文件路径和输出文件夹路径
input_tif = r'F:\wue\wue_OP\Wue_stacking.tif'
output_folder = r'F:\wue\wue_OP\blocks'

# 创建输出文件夹
os.makedirs(output_folder, exist_ok=True)

# 定义切片大小
tile_size = 1000

# 打开输入的TIF文件
with rasterio.open(input_tif) as src:
    width = src.width
    height = src.height
    profile = src.profile

    # 计算列和行的数量
    num_tiles_x = (width + tile_size - 1) // tile_size
    num_tiles_y = (height + tile_size - 1) // tile_size

    # 遍历行和列，切割小块
    for i in range(num_tiles_y):
        for j in range(num_tiles_x):
            # 计算窗口大小
            x_off = j * tile_size
            y_off = i * tile_size
            win_width = min(tile_size, width - x_off)
            win_height = min(tile_size, height - y_off)
            window = Window(x_off, y_off, win_width, win_height)

            # 更新元数据
            tile_profile = profile.copy()
            tile_profile.update({
                'height': win_height,
                'width': win_width,
                'transform': rasterio.windows.transform(window, src.transform)
            })

            # 读取窗口数据
            data = src.read(window=window)

            # 生成输出文件名
            tile_filename = f'tile_{i}_{j}.tif'
            tile_filepath = os.path.join(output_folder, tile_filename)

            # 保存小块
            with rasterio.open(tile_filepath, 'w', **tile_profile) as dst:
                dst.write(data)

print("切割完成，所有小块已保存到文件夹。")
