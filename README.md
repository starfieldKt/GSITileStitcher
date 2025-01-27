# What is Tile Map Stitcher

This tool allows you to download and stitch together Geospatial Information Authority (GSI) tiles (photos) at any zoom level within the grid range, and also creates a position information file for offline use of background images in the calculation area.

## Installation

Place the entire `GSITileStitcher` folder into `IRICROOT\private\solvers`.

## Usage

1. Create an appropriate grid for the area where you want the background image. (Rectangular grid generation tools are recommended)
2. Enter the coordinate system, zoom level, and save location in the calculation conditions.
3. Run the solver.


# タイルマップ取得結合ツールとは

計算領域の背景画像をオフラインでも使いたいときに、格子の範囲の任意のズームレベルの地理院タイル(写真)をダウンロード、結合し位置情報ファイルも作ってくれるツールです。

## インストール方法
`GSITileStitcher`フォルダーを`IRICROOT\private\solvers`にフォルダごと入れてください。

## 使い方

1. 背景画像が欲しい範囲に適当な格子を作ります。（矩形格子生成ツールなどがおすすめ）
2. 座標系、ズームレベル、保存先などを計算条件に入力します。
3. ソルバーを実行します。