import os
from osgeo import ogr

def extract_province_boundaries(input_shp_path, output_folder_path):
    # 打开输入shp文件
    driver = ogr.GetDriverByName('ESRI Shapefile')
    datasource = driver.Open(input_shp_path, 0)  # 0表示只读模式
    if datasource is None:
        print(f"无法打开文件: {input_shp_path}")
        return

    # 获取图层
    layer = datasource.GetLayer()
    
    # 获取字段定义
    layer_defn = layer.GetLayerDefn()
    field_names = [layer_defn.GetFieldDefn(i).GetName() for i in range(layer_defn.GetFieldCount())]
    print(f"字段名称: {field_names}")

    # 确认字段名称
    fid_column = 'FID'
    name_column = 'pr_name'

    # 创建输出文件夹
    if not os.path.exists(output_folder_path):
        os.makedirs(output_folder_path)

    # 遍历每个省份并创建单独的shp文件
    for feature in layer:
        fid = feature.GetFID()
        province_name = feature.GetField(name_column)

        if 0 <= fid <= 33:
            output_shp_path = os.path.join(output_folder_path, f"{province_name}.shp")

            # 创建输出shp文件
            out_driver = ogr.GetDriverByName('ESRI Shapefile')
            if out_driver is None:
                print("无法创建输出文件驱动程序。")
                continue

            out_datasource = out_driver.CreateDataSource(output_shp_path)
            if out_datasource is None:
                print(f"无法创建输出文件: {output_shp_path}")
                continue

            # 创建输出图层，使用相同的地理参考系统
            out_layer = out_datasource.CreateLayer(layer.GetName(), geom_type=layer.GetGeomType())

            # 复制字段定义
            for i in range(layer_defn.GetFieldCount()):
                out_layer.CreateField(layer_defn.GetFieldDefn(i))

            # 将要素写入输出图层
            out_layer.CreateFeature(feature)

            # 关闭输出数据源
            out_datasource = None

            print(f"省份 {province_name} 的边界已输出到 {output_shp_path}。")

    # 关闭输入数据源
    datasource = None

# 使用示例
input_shp_path = r'F:\trends\shp\ChinaAdminDivisonSHP\2. Province\province.shp'  # 输入shp文件路径
output_folder_path = r'F:\trends\shp\ChinaAdminDivisonSHP\Provinces'  # 输出文件夹路径
extract_province_boundaries(input_shp_path, output_folder_path)
