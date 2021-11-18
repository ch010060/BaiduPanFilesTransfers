BaiduPanFilesTransfers
-----
#### 介紹使用

百度網盤批量轉存工具,基於Python 3.8+Tkinter
詳細介紹使用請訪問:[小眾軟體](https://meta.appinn.net/t/topic/16995/39)

![1.9版本截圖](https://raw.githubusercontent.com/hxz393/BaiduPanFilesTransfers/master/Capture/%E6%88%AA%E5%9B%BE1.9.jpg)

**1.獲取Cookie和User-Agent:**

使用Chrome或類似瀏覽器訪問百度網盤主頁,完全載入后按F12調出控制檯,選擇網路(NetWork)選項卡,目前應該空空如也:
![嚮導圖1](https://raw.githubusercontent.com/hxz393/BaiduPanFilesTransfers/master/Capture/u-1.png)
按F5重新整理頁面,下面出現很多條記錄,點選home那條右邊會出現菜單,顯示標頭(Headers),響應(Response)等內容.看標頭裡往下翻找到Cookie專案,後面有一串以BAIDUID開頭的長長內容,這就是需要找的Cookies了,把它們選中全部複製出來貼上到軟體對應輸入框.
![嚮導圖2](https://raw.githubusercontent.com/hxz393/BaiduPanFilesTransfers/master/Capture/u-2.png)
再往下翻能看到User-Agent專案,同樣把它複製貼上到軟體對應輸入框便行了.軟體會自動儲存目前配置,下次無需再次操作.
![嚮導圖3](https://raw.githubusercontent.com/hxz393/BaiduPanFilesTransfers/master/Capture/u-3.png)

**2.輸入儲存目標和網盤鏈接:**

儲存目錄如果不輸入則儲存到根目錄下,儲存目錄不存在會自動新建.

鏈接支援格式:

*標準鏈接*
```
https://pan.baidu.com/s/1EFCrmlh0rhnWy8pi9uhkyA 提取碼：4444
https://pan.baidu.com/s/14Az6kqaluwtUDr5JH9WViA 提取:v70q
https://pan.baidu.com/s/1nvBwS25lENYceUu3OMH4tg 6img
https://pan.baidu.com/s/1EFCrmlh0rhnWy8pi9uhkyA
https://pan.baidu.com/share/init?surl=W7U9g47xiDez_5ItgNIs0w
```

*遊俠 v1標準*
```
https://pan.baidu.com/#bdlink=QkQyMTUxNjJENzE5NDc4QkNBRDJGMTMyNTlFMTEzNzAjRkJBMTEzQTY1M0QxN0Q1NjM3QUQ1MEEzRTgwMkE2QTIjMzcxOTgxOTIzI1pha3VybyAyMDAxMjYuN3oK
bdlink=QkQyMTUxNjJENzE5NDc4QkNBRDJGMTMyNTlFMTEzNzAjRkJBMTEzQTY1M0QxN0Q1NjM3QUQ1MEEzRTgwMkE2QTIjMzcxOTgxOTIzI1pha3VybyAyMDAxMjYuN3oK
```

*夢姬標準*
```
965FEAFCC6DC216CB56128B531694C9D#495B4FB5879AE0B22A31826D33D86D80#802846691#夢姬標準.7z
```

*Go格式*
```
BaiduPCS-Go rapidupload -length=418024594 -md5=31f141fee63d038a46db179367315f3a -slicemd5=5b2c842f421143a9a49938dc157c52e6 -crc32=3179342807 \"/音樂/Yes/1969. Yes.zip\"
```

*PanDL標準*
```
bdpan://44K344Or44Kv44Gu5p6c5a6fICsg44Go44KJ44Gu44GC44Gq44CA5o+P44GN5LiL44KN44GXOFDlsI/lhorlrZAg5pel5paHLnppcHw2NDAxODQxNTd8ZDNjOTBmOTI3ZjUxYzIyMmRjMTc1NDM1YTY0OWMyYTJ8OTk4NTE0NDE3Y2I5Y2I0MTQ0MGRlZTFiMmMyNTYwMzY=`
```

**3.注意事項:**

1.如在瀏覽器端登出百度賬號,再次登錄需要重新手動獲取Cookie值,否則會提示獲取不到bdstoken;

2.同一賬號在多瀏覽器登錄會導致獲取不到shareid.請退出所有賬號並重新打開唯一的瀏覽器登錄(建議使用Chrome)並獲取Cookie和User-Agent.
_ _ _
#### 下載使用
點到release頁面下載bpftUI.exe,直接打開使用
_ _ _
#### 自行打包
1. 克隆專案,在CMD中切換至專案目錄
2. 使用pyinstaller打包:
``
pyinstaller -F -w -i bpftUI.ico bpftUI.py
``
_ _ _
#### 更新日誌
**2020.05.09 更新版本 1.9**

1.修復可用性;

2.增加對舊式產生鏈接的支援;

3.增加cookie非法字元檢測.

**2020.12.15 更新版本 1.8**

修復可用性,修改部分用語

**2020.11.01 更新版本 1.7**

更進百度更新,修改鏈接驗證邏輯

**2020.09.14 更新版本 1.6**

修復無驗證碼分享資料夾鏈接轉存提示'驗證碼錯誤'問題

**2020.08.15 更新版本 1.5**

1.修復非檔案多檔案共享鏈接只轉存第一個檔案的問題;

2.增加User-Agent輸入框以應對百度網盤新一輪更新;

3.增加配置儲存功能.

**2020.08.12 更新版本 1.4**

修復百度更新后獲取不到bdstoken問題

**2020.07.26 更新版本 1.3**

修復部分秒傳鏈接無法識別問題

**2020.07.07 更新版本 1.2**

修復由於md5值大小寫原因造成的秒傳鏈接轉存失敗

**2020.06.19 更新版本 1.1**

增加對提取碼不正確,檔案已被刪除,彈出驗證碼狀態判斷

**2020.06.16 更新版本 1.0**

增加對資料夾和秒傳鏈接的支援

