## 🌐 Interactive Demo

[▶ Open Interactive 3D Visualization](https://rolanthhuang.github.io/Multi-dimensional-choices/wanted-unwanted-interactive.html)

# Wanted / Unwanted 多維度離散選擇機制

這個專案示範如何在一組相同的離散候選項目中，同時考慮「想要程度」與「不想要的風險」，最後找出兼顧偏好與低風險的候選項。

主要程式：

```text
main demo code/multi-dimensional-choices.py
```

> GitHub 版本的程式檔名是 `multi-dimensional-choices.py`。

## 核心概念

每個候選項 `i` 都有兩個分數：

- `wanted[i]`：偏好分數，數值越高代表越想要。
- `unwanted[i]`：風險分數，數值越高代表風險越高。

`wanted` 與 `unwanted` 使用完全相同的候選項 ID，因此同一個候選項可以在兩個維度中直接對照。

例如：

```python
wanted = {0: 45, 1: 30, 2: 48}
unwanted = {0: 20, 1: 5, 2: 40}
```

候選項 `2` 的 wanted 最高，但 unwanted 風險也最高；候選項 `0` 雖然偏好略低，卻可能是更平衡的選擇。

## 選擇流程

整體機制分成兩個階段。

### 1. Wanted：先找出我們比較想要的候選項

程式會將 wanted 分數排序，嘗試不同的高、低分群切點，並以平均平方距離尋找最合適的分群位置。

選定切點後，使用高分群的平均值作為 wanted 門檻：

```text
considered = 所有 wanted[i] >= wanted_threshold 的候選項
```

這些通過 wanted 階段的候選項會顯示為黃色。

### 2. Unwanted：在 wanted 結果中控制風險

只在 `considered` 候選項中計算與理想點的距離。

理想點定義為：

- wanted 等於目前最高 wanted 分數。
- unwanted risk 等於 0。

每個候選項的距離分數為：

```text
distance[i] = (max_wanted - wanted[i])² + unwanted[i]²
```

距離越小，表示越接近「高 wanted、低 unwanted risk」。

最後選出距離最小的候選項；若有多個候選項並列，程式會從並列結果中隨機選出一個作為 `fetch`。

```text
全部候選項
    │
    ▼
Wanted 高分群篩選
    │
    ▼
只保留 considered 候選項
    │
    ▼
比較 wanted 差距與 unwanted risk
    │
    ▼
fetch
```

## 顏色規則

同一個候選項在 wanted 與 unwanted 兩側使用相同顏色：

| 顏色 | 意義 |
|---|---|
| `crimson` | 最後選出的 `fetch` |
| `gold` | 通過 wanted 階段的候選項 |
| `#00ceaa` | 其他候選項 |

`fetch` 的 crimson 優先權最高。如果 fetch 同時屬於 wanted 高分群，兩側仍會顯示為 crimson。

## 3D 圖形設計

Wanted 與 Unwanted 共用同一個 `z=0` 平面：

- Wanted 從 `z=0` 朝上。
- Unwanted risk 從 `z=0` 朝下。
- 相同候選項在上下兩側使用相同的 `x, y` 位置。
- 因此可以直接看到一個候選項的 wanted 高度與 unwanted 深度。

Matplotlib 版本適合產生靜態圖片；Plotly HTML 版本可以：

- 按住滑鼠拖曳並旋轉 3D 視角。
- 使用滾輪縮放。
- 將游標移到柱體上查看候選項 ID、wanted 與 unwanted 數值。
- 從不同角度查看被其他柱體遮住的 fetch。

## 安裝需求

建議使用 Python 3.10 或更新版本。

```bash
python -m pip install numpy matplotlib plotly
```

## 執行方式

在 `main demo code` 目錄執行：

```bash
python "multi-dimensional-choices.py"
```

預設：

- `num_elements = 100`
- `columns = 10`
- 產生 `wanted_unwanted_interactive.html`
- 開啟 Matplotlib 3D 圖形

### 調整候選項數量

```bash
python "multi-dimensional-choices.py" --num-elements 150
```

### 指定亂數種子，讓結果可以重現

```bash
python "multi-dimensional-choices.py" --num-elements 100 --seed 42
```

### 只產生 HTML，不開啟 Matplotlib 視窗

```bash
python "multi-dimensional-choices.py" --no-show
```

### 同時輸出 PNG

```bash
python "multi-dimensional-choices.py" \
  --no-show \
  --html-output "wanted_unwanted_interactive.html" \
  --png-output "wanted_unwanted_combined.png"
```

### 不產生 HTML

```bash
python "multi-dimensional-choices.py" --no-html
```

## 在 Python 或 Jupyter 中使用

```python
import runpy

demo = runpy.run_path("multi-dimensional-choices.py")

demo["run_demo"](
    num_elements=100,
    seed=42,
    columns=10,
    html_output="wanted_unwanted_interactive.html",
    png_output="wanted_unwanted_combined.png",
    show=True,
)
```

也可以提供自己的 wanted / unwanted 資料：

```python
import random
import runpy

demo = runpy.run_path("multi-dimensional-choices.py")

wanted = {0: 45, 1: 30, 2: 48, 3: 40}
unwanted = {0: 20, 1: 5, 2: 40, 3: 8}

rng = random.Random(42)

fetch, considered, threshold, finalists = demo["choose_candidate"](
    wanted,
    unwanted,
    rng,
)

demo["plot_combined_matplotlib"](
    wanted,
    unwanted,
    considered,
    fetch,
    columns=2,
)

demo["write_interactive_html"](
    wanted,
    unwanted,
    considered,
    fetch,
    columns=2,
    html_output="wanted_unwanted_interactive.html",
)
```

## 主要參數

| 參數 | 預設值 | 說明 |
|---|---:|---|
| `--num-elements` | `100` | 候選項數量 |
| `--columns` | `10` | 3D 候選項網格的欄數 |
| `--seed` | 無 | 固定隨機資料與並列選擇結果 |
| `--html-output` | `wanted_unwanted_interactive.html` | HTML 輸出位置 |
| `--png-output` | 無 | 選擇性的 PNG 輸出位置 |
| `--no-html` | 關閉 | 不產生 Plotly HTML |
| `--no-show` | 關閉 | 不開啟 Matplotlib 視窗 |

## 資料與使用限制

目前示範資料使用 `0–50` 的隨機整數。實際使用時可以替換成真實的偏好與風險資料，但應先確保：

1. wanted 與 unwanted 使用相同的候選項 ID。
2. wanted 數值越高代表越偏好。
3. unwanted 數值越高代表風險越高。
4. 不同維度的量尺應具有可比較的尺度；若量尺差異很大，應先正規化或加入權重。

這是一個離散選擇與視覺化示範。實際風險控制決策仍需配合資料品質、權重設定、業務規則與驗證流程。
