<div align=center>
  
  <img width="200" alt="logo" src="https://github.com/user-attachments/assets/7bf8c1be-2abe-47d0-b8d9-78394a2a3312" />
  
  <h2>澪刻・在地化安裝器 Next</h2>
  
  [![stars](https://img.shields.io/github/stars/LocalizedKorabli/LKInstaller-Next.svg?style=for-the-badge)](https://github.com/LocalizedKorabli/LKInstaller-Next/stargazers)
  [![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-purple.svg?style=for-the-badge)](https://www.gnu.org/licenses/agpl-3.0)
  [![release](https://img.shields.io/github/release/LocalizedKorabli/LKInstaller-Next.svg?style=for-the-badge)](https://github.com/LocalizedKorabli/LKInstaller-Next/releases/latest)
  
  [![原始碼](https://img.shields.io/badge/專案-原始碼-orange?style=for-the-badge)](https://github.com/LocalizedKorabli/LKInstaller-Next/tree/dev)
  [![Discord](https://img.shields.io/discord/1275430075369656381?style=for-the-badge)](https://discord.gg/3d9k2mkWy4)
  [![QQ群](https://img.shields.io/badge/QQ-發布群-red?style=for-the-badge)](https://qm.qq.com/q/oLZZH47TRA)
  
</div>

<details><summary style="font-size: 14px;">Languages🌐</summary>

**繁體中文** | [English](/docs/en/README.md) | [简体中文](/README.md) | [Русский](/docs/ru/README.md) | [日本語](/docs/ja/README.md)

</details>

*本文由 AI 翻譯。可能存在錯誤或歧義。*

## 簡介

澪刻・在地化安裝器 Next （以下簡稱**澪刻 Next**）是對[澪刻・漢化安裝器](https://github.com/LocalizedKorabli/L10nInstallerGUI)的完全重寫。

<details><summary style="font-size: 12px;">澪刻 Next 新特性</summary>
<h4>相較於澪刻・漢化安裝器，澪刻 Next 引入的新功能：</h4>

- 支援安裝多種語言的在地化包：簡體中文、繁體中文、英文、日文；
- 支援為 Steam 上的 Mir Korabley 客戶端安裝在地化包；
- 支援解除安裝在地化包；
- 支援安裝字型優化包，在地化語言設定為簡體中文/繁體中文/日文時此選項預設啟用；
- 支援應用程式本體一鍵更新；
- 引入「實例」和「設定檔」，現在支援為多個遊戲客戶端實例同時執行不同的安裝/解除安裝操作；
- 支援同時使用多條下載線路，並對後者進行優先級排序；
  - 支援的線路：
    - 騰訊雲（僅字型優化包和應用程式更新包）
    - Cloudflare （僅字型優化包和應用程式更新包）
    - Gitee 碼雲（僅在地化包和體驗增強包）
    - GitLab （僅在地化包和體驗增強包）
    - GitHub （僅在地化包和體驗增強包）
- 支援更細緻地調節代理伺服器選項；
- 支援切換應用程式介面語言、淺色/深色主題。

<h4>相較於澪刻・漢化安裝器，澪刻 Next 的功能改動：</h4>

- 版本識別機制已被最佳化，現在總是只為遠端倉庫定義的作用中版本安裝在地化包；
- 所有內容現在均以 Mir Korabley 新引入的 .mkmod 格式安裝；
- 在地化修改包（原漢化修改包）現在總是以 Mir Korabley 新引入的「MO 掛載」機制安裝。

<h4>相較於澪刻・漢化安裝器，澪刻 Next 刪除的功能：</h4>

- 由於極少被使用且易於誤導使用者，向直營服/國服安裝在地化包的功能已被刪除。

</details>

## 下載並安裝澪刻 Next

### 下載線路
- [官方下載頁面](https://localizedkorabli.org/cht/lk-next.html)

<details><summary style="font-size: 12px;"><b>瀏覽器阻止下載時的操作方法</b></summary>

- Microsoft Edge （通常不會下載 lki_setup.exe。請在開啟前確保信任 lki_setup.exe ）：
  - 將滑鼠移至檔案對應的下載項目上，點擊在右側出現的以「3 個點」（...）為圖示的按鈕，再點擊**保留**選項；
  - 彈出「開啟前請確保信任 lki_setup.exe」子視窗後，從藍色**刪除**按鈕最右側開啟下拉列，點擊**仍然保留**選項。

- Chrome （已阻止可疑下載操作）：
  - 點擊檔案對應的下載項目，再點擊**下載可疑檔案**選項。

</details>

### 安裝應用程式
- 開啟您下載的安裝包檔案，選擇安裝時使用的語言（此語言也會被設為澪刻 Next 的預設顯示語言及安裝在地化包的預設語言），並根據指示完成安裝。

## 使用澪刻 Next

### 省流

如果您只需要安裝在地化包而不需要進行任何額外設定，直接點擊應用程式主介面（**遊戲**頁）左下角的**安裝**按鈕即可。

### 實例

#### 什麼是實例？

您安裝的 Mir Korabley 客戶端可被作為「實例」匯入應用程式，以便安裝在地化包。

#### 匯入實例

首次啟動時，應用程式會嘗試掃描裝置上所有 Mir Korabley 客戶端，並作為實例匯入。

若列表中未出現您想要的實例，請先確保遊戲已完整安裝，然後點擊「遊戲實例」標籤行最右側的**自動匯入電腦上的實例**按鈕。

若仍未匯入，請點擊同一標籤行的**匯入實例**按鈕，嘗試手動匯入遊戲實例。

#### 管理實例

您可以在**遊戲**頁檢視目前已匯入的所有遊戲實例。

您還可以透過**遊戲**頁的其他按鈕對實例進行匯入、快速編輯、移除、排序、開啟所在資料夾、執行遊戲、生成自動更新捷徑等操作。

#### 選中實例（用於檢視實例詳細資訊）

點擊遊戲實例的名稱來選中它。選中後，該實例項目將被藍色高亮。您可以切換到**進階**頁，檢視實例以及當前選中設定檔的詳細資訊。

#### 勾選實例（用於安裝/解除安裝在地化包）

點擊**遊戲**頁左側與遊戲實例列表項目平齊的核取方塊，以勾選/取消勾選實例。點擊「遊戲實例」標籤行的核取方塊能一次性勾選/取消勾選所有實例。

所有新匯入的實例預設被勾選。

### 設定檔

#### 什麼是設定檔？

一個實例可以擁有多個「設定檔」，後者決定著應用程式**在為實例安裝在地化包過程中執行的具體操作**：

- 下載並安裝何種**語言/客戶端類型**（正式服、測試服）的在地化包
- 是否下載並安裝[**體驗增強包**](#體驗增強包)
- 是否下載並安裝[**字型優化包**](#字型優化包)
- 是否載入[**在地化修改包**](#在地化修改包)

#### 預設設定檔

每一個實例都有一個**預設設定檔**（初始設定），其中在地化的安裝語言被預設設定為**使用者匯入實例時應用程式正在顯示的語言**。

#### 管理設定檔

要管理設定檔，請先選中一個遊戲實例，然後切換到**進階**頁。

在設定檔組態標籤框架下名為**安裝設定檔**的下拉選單中，您可以快速切換設定檔。

點擊下拉選單右側的齒輪按鈕，可進入**管理設定檔**介面。

在設定檔管理介面中，您可以：
- 對該實例的設定檔本身進行增刪改等操作；
- 變更設定檔的各項設定；
- 為當前設定檔生成**自動更新捷徑**。

### 自訂

#### 體驗增強包

體驗增強包是一組適用於 Mir Korabley 的模組，其中包含：
- [輸入法支援模組](https://bbs.nga.cn/read.php?tid=29102783)；
- 基於 Unbound 框架的 UI 最佳化模組；
- 基於當前在地化語言的、對其他 Mir Korabley 模組的翻譯修補模組；
- 帶有本團隊標識的開屏 Logo 修補。

預設設定檔下將會安裝體驗增強包，您也可以在**管理設定檔**介面中選擇是否安裝它。

#### 字型優化包

字型優化包是適用於 Mir Korabley 的字型最佳化模組，其中包含了 SrcWagon——基於 Mir Korabley 原生字型「ALS Wagon」和「Source Han Sans CN」製作的新字型，修復了部分字形的外觀與位置。

當您設定檔中的在地化語言設定為**簡體中文**、**繁體中文**或**日文**時，將預設安裝字型優化包，您也可以在**管理設定檔**介面中選擇是否安裝它。

#### 在地化修改包

在地化修改包用於對在地化包的部分文字進行修改。關於在地化修改包的製作，請查閱 [Mir Korabley 論壇上的文章](https://forum.korabli.su/topic/162025-)。

您可以將已製作的在地化修改包直接拖入或是打包到 zip 檔案後放入（透過點擊**管理設定檔**介面中的資料夾圖示按鈕開啟的）當前設定檔所使用的在地化修改包資料夾。

在地化修改包將在您**下一次**安裝在地化包時被載入。

預設設定檔下將會安裝在地化修改包，您也可以在**管理設定檔**介面中選擇是否安裝它。

### 應用程式設定

在**設定**頁中，您可以：
- 調整應用程式的**外觀**、**下載**、**檔案**相關設定；
- 清除下載快取和輸出日誌；
- 檢視應用程式的資料目錄。

### 應用程式資訊

在**關於**頁中，您可以：
- 檢視應用程式的版本，並為應用程式**檢查更新**；
- 透過點擊圖示為 GitHub、QQ、Discord 的按鈕來存取此應用程式的原始碼倉庫或加入本團隊在對應社交平台上的群組；
- 透過點擊版權標註資訊上方的紫色「AGPL V3」圖示來跳轉到 GNU 的官方網頁，以檢視本應用程式授權條款的全文。

## Q&A

### 應用程式出現報錯或在地化包安裝失敗怎麼辦？

請先嘗試[**檢查更新**](#應用程式資訊)後重新安裝在地化包。

點擊**設定**頁，點擊**應用程式資料路徑**行的**開啟目錄**按鈕。在被開啟的資料夾中，進入 logs 資料夾，並儲存好最新的 .log 檔案。

您可以開啟該檔案嘗試分析報錯原因並自行修復，或將檔案提交到 [GitHub Issues](https://github.com/LocalizedKorabli/LKInstaller-Next/issues) | [QQ群](https://qm.qq.com/q/SUoZAcV442) | [Discord 伺服器](https://discord.gg/3d9k2mkWy4) 以尋求幫助。

### 自動更新功能去哪裡了？

請見[管理實例](#管理實例)和[管理設定檔](#管理設定檔)。您可以在**遊戲**頁或**管理設定檔**介面中為實例生成**自動更新捷徑**。

### 對在地化包本身有疑問怎麼辦？

請根據您所使用的語言和客戶端類型，在[團隊主頁傳送門](https://github.com/LocalizedKorabli#%E9%A0%85%E7%9B%AE%E5%82%B3%E9%80%81%E9%96%80portal)中找到相關的倉庫，並在其 Issues 中提交回饋。

您也可以加入 QQ 群或 Discord 伺服器參與討論。

## 鳴謝

- 參與本專案內部測試的所有使用者

- [Python](https://www.python.org/)——本應用程式所使用的程式語言

- [Tkinter](https://docs.python.org/3/library/tkinter.html)——本應用程式所使用的 GUI 框架

- [Google Gemini](https://gemini.google.com/)、[Claude Code](https://claude.ai/code)、[DeepSeek](https://deepseek.com/)——將本應用程式的開發時間縮短了約 80%

- [Azure theme for ttk](https://github.com/rdbende/Azure-ttk-theme)——本應用程式介面所使用的 ttk 主題

- [Inno Setup](https://jrsoftware.org/isinfo.php)、[Nuitka](https://nuitka.net/)——為本應用程式提供了便捷的打包方案
