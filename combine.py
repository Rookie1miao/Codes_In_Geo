import os
import rasterio
from rasterio.merge import merge

# 输入小块文件夹路径和输出大TIF文件路径
input_folder = r'F:\wue\wue_OP\std_tiles1'
output_tif = r'F:\wue\wue_OP\Wue_std_New.tif'

# 搜集所有小块的文件路径
tile_files = [os.path.join(input_folder, fname) for fname in os.listdir(input_folder) if fname.endswith('.tif')]

# 打开所有小块文件
src_files_to_mosaic = []
for fp in tile_files:
    src = rasterio.open(fp)
    src_files_to_mosaic.append(src)

# 拼接小块
mosaic, out_trans = merge(src_files_to_mosaic)

# 更新元数据
out_meta = src_files_to_mosaic[0].meta.copy()
out_meta.update({
    'height': mosaic.shape[1],
    'width': mosaic.shape[2],
    'transform': out_trans
})

# 保存拼接后的大TIF文件
with rasterio.open(output_tif, 'w', **out_meta) as dest:
    dest.write(mosaic)

print("拼接完成，已生成大TIF文件。")
