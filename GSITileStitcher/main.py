import iric
import GSITileStitcher
import sys

url_templates = {
    "1": "https://cyberjapandata.gsi.go.jp/xyz/std/{z}/{x}/{y}.png",
    "2": "https://cyberjapandata.gsi.go.jp/xyz/pale/{z}/{x}/{y}.png",
    "3": "https://cyberjapandata.gsi.go.jp/xyz/ort/{z}/{x}/{y}.jpg",
    "4": "https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
    "5": "https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}"
}

###############################################################################
# Main
# CGNSファイルから格子の4隅の座標を取得し、GSITileStitcherを用いてタイル画像を生成する
################################################################################

print("----------Start----------")

###############################################################################
# CGNSを開く
###############################################################################

# iRICで動かす時用
# =============================================================================
if len(sys.argv) < 2:
    print("Error: CGNS file name not specified.")
    exit()

cgns_name = sys.argv[1]

print("CGNS file name: " + cgns_name)

# CGNSをオープン
fid = iric.cg_iRIC_Open(cgns_name, iric.IRIC_MODE_MODIFY)

# コマンドラインで動かす時用
# =============================================================================

# CGNSをオープン
# fid = iric.cg_iRIC_Open("./project/Case1.cgn", iric.IRIC_MODE_MODIFY)

###############################################################################
# 格子を読み込み
###############################################################################

# 格子サイズを読み込み
isize, jsize = iric.cg_iRIC_Read_Grid2d_Str_Size(fid)

# 格子点の座標読み込み
grid_x_arr, grid_y_arr = iric.cg_iRIC_Read_Grid2d_Coords(fid)
grid_x_arr = grid_x_arr.reshape(jsize, isize).T
grid_y_arr = grid_y_arr.reshape(jsize, isize).T

# 格子の配列全体から最大最小を求める
x_min = grid_x_arr.min()
x_max = grid_x_arr.max()
y_min = grid_y_arr.min()
y_max = grid_y_arr.max()

print("Successfully read grid coordinates")
print("x_min: " + str(x_min) + " y_min: " + str(y_min))
print("x_max: " + str(x_max) + " y_max: " + str(y_max))

###############################################################################
# 計算条件の読み込み
###############################################################################

url_template_index = iric.cg_iRIC_Read_Integer(fid, "url_template_index")
epsg_code = iric.cg_iRIC_Read_Integer(fid, "epsg_code")
zoom_level = iric.cg_iRIC_Read_Integer(fid, "zoom_level")
output_filename = iric.cg_iRIC_Read_String(fid, "output_filename") + ".png"
output_directory = iric.cg_iRIC_Read_String(fid, "output_directory")

url_template = url_templates[str(url_template_index)]

print("Successfully read calculation conditions")
print("epsg_code: " + str(epsg_code))
print("zoom_level: " + str(zoom_level))
print("output_filename: " + output_filename)
print("output_directory: " + output_directory)
print("url_template: " + url_template)

###############################################################################
# タイル画像の生成
###############################################################################

GSITileStitcher.download_and_stitch(x_min, y_min, x_max, y_max, epsg_code, zoom_level, output_directory, output_filename, url_template)

print("----------finish----------")