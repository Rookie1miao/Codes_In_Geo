import rasterio
import rasterio.features
import geopandas as gpd
import numpy as np
import pandas as pd
import os
output_csv = r'D:\wue\Output\2000_Output.csv'
tif_file = r'D:\wue\Staked_Data\2000_allbands.tif'
shp_folder = r'D:\wue\Provinces'
with rasterio.open(tif_file) as src:
    # 以掩膜数组的形式读取数据和 LULC 波段
    data_band = src.read(1, masked=True)
    lulc_band = src.read(2, masked=True)
    transform = src.transform
    raster_crs = src.crs

# LULC 代码与标签的映射
lulc_labels = {
    1: "Rainfed cropland",
    2: "Herbaceous cover cropland",
    3: "Tree or shrub cover (Orchard) cropland",
    4: "Irrigated cropland",
    5: "Open evergreen broadleaved forest",
    6: "Closed evergreen broadleaved forest",
    7: "Open deciduous broadleaved forest (0.15<fc<0.4)",
    8: "Closed deciduous broadleaved forest (fc>0.4)",
    9: "Open evergreen needle-leaved forest (0.15< fc <0.4)",
    10: "Closed evergreen needle-leaved forest (fc >0.4)",
    11: "Open deciduous needle-leaved forest (0.15< fc <0.4)",
    12: "Closed deciduous needle-leaved forest (fc >0.4)",
    13: "Open mixed leaf forest (broadleaved and needle-leaved)",
    14: "Closed mixed leaf forest (broadleaved and needle-leaved)",
    15: "Shrubland",
    16: "Evergreen shrubland",
    17: "Deciduous shrubland",
    18: "Grassland",
    19: "Lichens and mosses",
    20: "Sparse vegetation (fc<0.15)",
    21: "Sparse shrubland (fc<0.15)",
    22: "Sparse herbaceous (fc<0.15)",
    23: "Swamp",
    24: "Marsh",
    25: "Flooded flat",
    26: "Saline",
    27: "Mangrove",
    28: "Salt marsh",
    29: "Tidal flat",
    30: "Impervious surfaces",
    31: "Bare areas",
    32: "Consolidated bare areas",
    33: "Unconsolidated bare areas",
    34: "Water body",
    35: "Permanent ice and snow",
    36: "Filled value"
}

# 从 LULC 波段获取唯一的 LULC 类型，并排除 36 及以上的值
lulc_types = np.unique(lulc_band.compressed())
lulc_types = lulc_types[lulc_types <= 35]

# 准备收集结果
results = []

# 获取 shapefile 路径列表
shp_files = [os.path.join(shp_folder, f) for f in os.listdir(shp_folder) if f.endswith('.shp')]

# 遍历每个 shapefile
for shp_file in shp_files:
    shp_name = os.path.splitext(os.path.basename(shp_file))[0]
    # 读取 shapefile
    gdf = gpd.read_file(shp_file)
    # 检查 CRS 是否已定义
    if gdf.crs is None:
        print(f"Shapefile {shp_name} 的 CRS 未定义。将其设置为 EPSG:4326。")
        # 设置 CRS 为 EPSG:4326
        gdf.set_crs('EPSG:4326', inplace=True)
    # 确保 CRS 与栅格数据一致
    if gdf.crs != raster_crs:
        print(f"将 shapefile {shp_name} 重投影以匹配栅格数据的 CRS。")
        gdf = gdf.to_crs(raster_crs)
    # 生成 shapefile 几何体的掩膜
    geoms = gdf.geometry.values
    mask = rasterio.features.geometry_mask(geometries=geoms,
                                           out_shape=data_band.shape,
                                           transform=transform,
                                           invert=True)
    # 对数据和 LULC 波段应用掩膜
    data_band_masked = np.ma.array(data_band, mask=~mask)
    lulc_band_masked = np.ma.array(lulc_band, mask=~mask)
    # 初始化字典保存每个 LULC 类型的平均数据值
    lulc_data = {}
    for lulc_type in lulc_types:
        # 获取 LULC 类型的标签
        lulc_label = lulc_labels.get(lulc_type, f"LULC_{lulc_type}")
        # 创建当前 LULC 类型的掩膜
        lulc_mask = (lulc_band_masked == lulc_type)
        # 提取对应当前 LULC 类型的数据值
        data_values = data_band_masked[lulc_mask]
        # 计算平均值
        if data_values.size > 0:
            avg_value = data_values.mean()
        else:
            avg_value = 0
        # 存储平均值
        lulc_data[lulc_label] = avg_value
    # 添加结果
    result = {'shp': shp_name}
    result.update(lulc_data)
    results.append(result)

# 创建 DataFrame
df = pd.DataFrame(results)
# 用 0 填充缺失值
df = df.fillna(0)
# 重新排列列顺序，只保留需要的列
ordered_labels = [lulc_labels[i] for i in range(1, 36)]  # LULC 代码从 1 到 35
columns = ['shp'] + ordered_labels
df = df.reindex(columns=columns, fill_value=0)
df.to_csv(output_csv, index=False)
