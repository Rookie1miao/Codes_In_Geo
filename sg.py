import os
import numpy as np
from osgeo import gdal
from scipy.stats import zscore
from scipy.signal import savgol_filter
from concurrent.futures import ProcessPoolExecutor, as_completed

def apply_zscore_anomaly_detection(data, zscore_threshold=2):
    band_count, height, width = data.shape
    processed_data = np.zeros_like(data, dtype=np.float32)

    for i in range(height):
        for j in range(width):
            pixel_values = data[:, i, j]
            zscores = zscore(pixel_values)
            outliers = np.abs(zscores) > zscore_threshold

            if np.any(outliers):
                mean_value = np.mean(pixel_values[~outliers])
                pixel_values[outliers] = mean_value
            
            processed_data[:, i, j] = pixel_values

    return processed_data

def apply_sg_filter_per_pixel(data, window_length=15, polyorder=2):
    band_count, height, width = data.shape
    filtered_data = np.zeros_like(data, dtype=np.float32)

    for i in range(height):
        for j in range(width):
            pixel_series = data[:, i, j]
            filtered_series = savgol_filter(pixel_series, window_length=window_length, polyorder=polyorder, mode='nearest')
            filtered_data[:, i, j] = filtered_series

    return filtered_data

def process_single_tif_file(input_tif_path, output_tif_path, zscore_threshold=2, window_length=15, polyorder=2):
    dataset = gdal.Open(input_tif_path, gdal.GA_ReadOnly)
    band_count = dataset.RasterCount
    width = dataset.RasterXSize
    height = dataset.RasterYSize

    data = np.zeros((band_count, height, width), dtype=np.float32)
    for i in range(band_count):
        band = dataset.GetRasterBand(i + 1)
        data[i, :, :] = band.ReadAsArray()

    processed_data = apply_zscore_anomaly_detection(data, zscore_threshold)
    filtered_data = apply_sg_filter_per_pixel(processed_data, window_length, polyorder)

    driver = gdal.GetDriverByName('GTiff')
    out_dataset = driver.Create(output_tif_path, width, height, band_count, gdal.GDT_Float32)
    out_dataset.SetGeoTransform(dataset.GetGeoTransform())
    out_dataset.SetProjection(dataset.GetProjection())

    for i in range(band_count):
        out_band = out_dataset.GetRasterBand(i + 1)
        out_band.WriteArray(filtered_data[i, :, :])
        out_band.FlushCache()

    del out_dataset
    print(f"Processed and saved {input_tif_path} to {output_tif_path}")

def process_tif_files(input_folder, output_folder, zscore_threshold=2, window_length=15, polyorder=2, max_workers=4):
    os.makedirs(output_folder, exist_ok=True)
    tif_files = [f for f in os.listdir(input_folder) if f.endswith('.tif')]

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for filename in tif_files:
            input_tif_path = os.path.join(input_folder, filename)
            output_tif_path = os.path.join(output_folder, filename)
            futures.append(executor.submit(process_single_tif_file, input_tif_path, output_tif_path, zscore_threshold, window_length, polyorder))

        for future in as_completed(futures):
            future.result()  # 等待每个任务完成并获取其结果

if __name__ == '__main__':
    # 示例使用
    input_folder = r'F:\SMA\IS1'  # 输入文件夹路径
    output_folder = r'F:\SMA\IS_SG'  # 输出文件夹路径

    process_tif_files(input_folder, output_folder, zscore_threshold=1.5, window_length=15, polyorder=2, max_workers=15)
