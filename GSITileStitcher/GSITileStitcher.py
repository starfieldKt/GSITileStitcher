import math
import os
import requests
from PIL import Image
from pyproj import CRS, Transformer
import shutil

def reset_tile_cache(output_dir):
    """
    タイルキャッシュをリセット
    """
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir)

def latlon_to_tile(lat, lon, zoom):
    """
    緯度経度をタイル座標に変換
    Args:
        lat (float): 緯度
        lon (float): 経度
        zoom (int): ズームレベル
    Returns:
        tuple: タイルのX座標とY座標
    """
    lat_rad = math.radians(lat)
    n = 2.0 ** zoom
    xtile = int((lon + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.log(math.tan(lat_rad) + 1 / math.cos(lat_rad)) / math.pi) / 2.0 * n)
    return xtile, ytile

def tile_to_latlon(xtile, ytile, zoom):
    """
    タイル座標を緯度経度に変換
    Args:
        xtile (int): タイルのX座標
        ytile (int): タイルのY座標
        zoom (int): ズームレベル
    Returns:
        tuple: 経度と緯度
    """
    n = 2.0 ** zoom
    lon = xtile / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
    lat = math.degrees(lat_rad)
    return lon, lat

def epsg_to_latlon(x, y, from_epsg):
    """
    指定EPSG座標系から緯度経度に変換
    Args:
        x (float): 変換前のX座標
        y (float): 変換前のY座標
        from_epsg (int): 変換元のEPSGコード
    Returns:
        tuple: 緯度経度
    """
    crs_from = CRS.from_epsg(from_epsg)
    crs_to = CRS.from_epsg(4326)
    transformer = Transformer.from_crs(crs_from, crs_to, always_xy=True)
    lon, lat = transformer.transform(x, y)
    return lat, lon

def latlon_to_epsg(lon, lat, to_epsg):
    """
    緯度経度を指定EPSG座標系に変換
    Args:
        lon (float): 経度
        lat (float): 緯度
        to_epsg (int): 変換先のEPSGコード
    Returns:
        tuple: 変換後のX座標とY座標
    """
    crs_from = CRS.from_epsg(4326)
    crs_to = CRS.from_epsg(to_epsg)
    transformer = Transformer.from_crs(crs_from, crs_to, always_xy=True)
    x, y = transformer.transform(lon, lat)
    return x, y

def download_tile(z, x, y, output_dir, url_template):
    """
    タイルをダウンロード
    Args:
        z (int): ズームレベル
        x (int): タイルのX座標
        y (int): タイルのY座標
        output_dir (str): タイル画像を保存するディレクトリ
        url_template (str): タイル画像のURLテンプレート
    """

    # タイル画像のURL
    url = url_template.format(z=z, x=x, y=y)
    print(f"Downloading tile: {url}")
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        filename = os.path.join(output_dir, f"{z}_{x}_{y}.png")
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
        print(f"Downloaded: {filename}")
        return filename
    else:
        print(f"Failed to download tile: {z}/{x}/{y}, Status Code: {response.status_code}")
        return None

def stitch_tiles(tiles, output_file):
    """
    タイル画像を結合
    Args:
        tiles (list): タイル画像のファイルパスとタイル座標のリスト
        output_file (str): 結合画像のファイル名
    """
    if not tiles:
        print("No tiles were downloaded. Exiting...")
        return

    images = [Image.open(tile[0]) for tile in tiles if tile[0]]
    if not images:
        print("No valid images found to stitch. Exiting...")
        return

    widths, heights = zip(*(img.size for img in images))
    grid_width = max(widths) * len(set(tile[1] for tile in tiles))
    grid_height = max(heights) * len(set(tile[2] for tile in tiles))
    stitched_image = Image.new('RGBA', (grid_width, grid_height))

    for file_path, x_offset, y_offset in tiles:
        img = Image.open(file_path).convert('RGBA')
        stitched_image.paste(img, (x_offset * max(widths), y_offset * max(heights)), img)

    stitched_image.save(output_file)
    print(f"Saved stitched image to {output_file}")

def create_jgw_file(min_x_tile, min_y_tile, zoom, output_file, target_epsg):
    """
    JGWファイルを生成
    Args:
        min_x_tile (int): 結合画像の左上タイルのX座標
        min_y_tile (int): 結合画像の左上タイルのY座標
        zoom (int): ズームレベル
        tile_size (int): タイルサイズ（ピクセル単位、通常256）
        output_file (str): JGWファイルを保存するファイルパス
        target_epsg (int): 出力する座標系のEPSGコード
    """
    lon_origin, lat_origin = tile_to_latlon(min_x_tile, min_y_tile, zoom)

    # 緯度経度からターゲットEPSGの座標系に変換
    x_origin, y_origin = latlon_to_epsg(lon_origin, lat_origin, target_epsg)

    # 緯度に基づく解像度の計算
    latitude = math.radians(lat_origin)
    map_resolution = 156543.04 * math.cos(latitude) / (2 ** zoom)

    jgw_content = [
        map_resolution,  # 1ピクセルの幅
        0.0,             # 回転（X方向、通常0）
        0.0,             # 回転（Y方向、通常0）
        -map_resolution, # 1ピクセルの高さ（負の値）
        x_origin,        # 左上のX座標
        y_origin         # 左上のY座標
    ]

    jgw_file = os.path.splitext(output_file)[0] + ".jgw"
    with open(jgw_file, 'w') as f:
        f.writelines(f"{value}\n" for value in jgw_content)

    print(f"Saved JGW file to {jgw_file}")

def download_and_stitch(x_min, y_min, x_max, y_max, epsg, zoom, output_dir, output_file, url_template):
    """
    指定範囲のタイルをダウンロードして結合
    Args:
        x_min (float): 最小X座標
        y_min (float): 最小Y座標
        x_max (float): 最大X座標
        y_max (float): 最大Y座標
        epsg (int): EPSGコード
        zoom (int): ズームレベル
        output_dir (str): タイル画像を保存するディレクトリ
        output_file (str): 結合画像のファイル名
        url_template (str): タイル画像のURLテンプレート
    """
    reset_tile_cache(output_dir)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    lat_min, lon_min = epsg_to_latlon(x_min, y_min, epsg)
    lat_max, lon_max = epsg_to_latlon(x_max, y_max, epsg)

    x_tile_min, y_tile_min = latlon_to_tile(lat_min, lon_min, zoom)
    x_tile_max, y_tile_max = latlon_to_tile(lat_max, lon_max, zoom)

    if y_tile_min > y_tile_max:
        y_tile_min, y_tile_max = y_tile_max, y_tile_min

    tiles = []
    for x in range(x_tile_min, x_tile_max + 1):
        for y in range(y_tile_min, y_tile_max + 1):
            tile_path = download_tile(zoom, x, y, output_dir, url_template)
            if tile_path:
                tiles.append((tile_path, x - x_tile_min, y - y_tile_min))

    if tiles:
        stitch_tiles(tiles, output_file)
        create_jgw_file(
            x_tile_min, y_tile_min, zoom, output_file, epsg
        )
    else:
        print("No tiles downloaded. Check the input parameters or network connection.")

if __name__ == "__main__":
    min_x_coord = -70505.966631
    min_y_coord = -100119.011746
    max_x_coord = -69251.961035
    max_y_coord = -99029.561672
    epsg_code = 6680
    zoom_level = 16
    output_directory = "./tiles"
    output_filename = "stitched_image.png"
    url_template = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"

    download_and_stitch(
        min_x_coord, min_y_coord, max_x_coord, max_y_coord,
        epsg_code, zoom_level, output_directory, output_filename, url_template
    )

# EPSGコード
    # EPSG:6669 - JGD2011 / Japan Plane Rectangular CS I
    # EPSG:6670 - JGD2011 / Japan Plane Rectangular CS II
    # EPSG:6671 - JGD2011 / Japan Plane Rectangular CS III
    # EPSG:6672 - JGD2011 / Japan Plane Rectangular CS IV
    # EPSG:6673 - JGD2011 / Japan Plane Rectangular CS V
    # EPSG:6674 - JGD2011 / Japan Plane Rectangular CS VI
    # EPSG:6675 - JGD2011 / Japan Plane Rectangular CS VII
    # EPSG:6676 - JGD2011 / Japan Plane Rectangular CS VIII
    # EPSG:6677 - JGD2011 / Japan Plane Rectangular CS IX
    # EPSG:6678 - JGD2011 / Japan Plane Rectangular CS X
    # EPSG:6679 - JGD2011 / Japan Plane Rectangular CS XI
    # EPSG:6680 - JGD2011 / Japan Plane Rectangular CS XII
    # EPSG:6681 - JGD2011 / Japan Plane Rectangular CS XIII
    # EPSG:6682 - JGD2011 / Japan Plane Rectangular CS XIV
    # EPSG:6683 - JGD2011 / Japan Plane Rectangular CS XV
    # EPSG:6684 - JGD2011 / Japan Plane Rectangular CS XVI
    # EPSG:6685 - JGD2011 / Japan Plane Rectangular CS XVII
    # EPSG:6686 - JGD2011 / Japan Plane Rectangular CS XVIII
    # EPSG:6687 - JGD2011 / Japan Plane Rectangular CS XIX