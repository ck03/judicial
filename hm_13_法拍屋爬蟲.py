import requests
import json
from lxml import etree
import re


class LowHouseSpider(object):

    def proptypename(self, proptypecode):
        proptype = {"C52": "房屋", "C51": "土地", "C54": "動產"}
        return proptype[proptypecode]

    def courtname(self, courtcode):
        court = {"TPD": "臺灣台北地方法院",
                 "PCD": "臺灣新北地方法院",
                 "SLD": "臺灣士林地方法院",
                 "TYD": "臺灣桃園地方法院",
                 "SCD": "臺灣新竹地方法院",
                 "MLD": "臺灣苗栗地方法院",
                 "TCD": "臺灣臺中地方法院",
                 "NTD": "臺灣南投地方法院",
                 "CHD": "臺灣彰化地方法院",
                 "ULD": "臺灣雲林地方法院",
                 "CYD": "臺灣嘉義地方法院",
                 "TND": "臺灣臺南地方法院",
                 "CTD": "臺灣橋頭地方法院",
                 "KSD": "臺灣高雄地方法院",
                 "PTD": "臺灣屏東地方法院",
                 "TTD": "臺灣臺東地方法院",
                 "HLD": "臺灣花蓮地方法院",
                 "ILD": "臺灣宜蘭地方法院",
                 "KLD": "臺灣基隆地方法院",
                 "PHD": "臺灣澎湖地方法院",
                 "KMD": "福建金門地方法院",
                 "LCD": "福建連江地方法院"
                 }
        return court[courtcode]

    def __init__(self, court, proptype):
        self.court = court
        self.proptype = proptype
        self.url_page1 = "http://aomp.judicial.gov.tw/abbs/wkw/WHD2A03.jsp?8EFF1B4C068B4B0AA29B5128C9384BCD=4E894B4C2C2F342C30964295C7EF87E6&hsimun=all&ctmd=all&sec=all&saledate1=&saledate2=&crmyy=&crmid=&crmno=&dpt=&minprice1=&minprice2=&saleno=&area1=&area2=&registeno=&checkyn=all&emptyyn=all&rrange=%A4%A3%A4%C0&comm_yn=&owner1=&order=odcrm&courtX={}&proptypeX={}&saletypeX=1&query_typeX=db"
        self.url_nextpage = "http://aomp.judicial.gov.tw/abbs/wkw/WHD2A03.jsp?pageTotal={}&pageSize=15&rowStart={}&saletypeX=1&courtX={}&proptypeX={}&order=odcrm&query_typeX=session&saleno=&hsimun=all&ctmd=all&sec=all&crmyy=&crmid=&crmno=&dpt=&saledate1=&saledate2=&minprice1=&minprice2=&sumprice1=&sumprice2=&area1=&area2=&registeno=&checkyn=all&emptyyn=all&order=odcrm&owner1=&landkd=&rrange=%A4%A3%A4%C0&comm_yn=&stopitem=&courtNoLimit=&pageNow={}&0A9A9390C7CA7C6D4D1ECCB486FED036=7FA43DE606C320A88A31A46B7DD028EF"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36"}
        self.dict_info = {}
        self.list_info = []

    def parse_url(self, url):
        response = requests.get(url, headers=self.headers)
        # 直接用response.content.decode()有 'utf-8' codec can't decode byte 這個問題,
        # 雖然response.content.decode("utf8","ignore")加了"ignore"可以過,但這個
        # 爬出來的資料卻是亂碼,所以要改為big5就可以過,連"ignore"都可以不用加
        ret = response.content.decode("big5", "ignore")
        return ret

    def combinejson(self, seq):
        if self.proptype == "C52":
            seq_list = ["筆次", "法院名稱", "字號(股別)", "拍賣日期拍賣次數", "縣市", "房屋地址/樓層面積", "總拍賣底價(元)", "點交", "空屋", "標別", "備註", "看圖", "採通訊投標", "土地有無遭受污染"]
        elif self.proptype == "C51":
            seq_list = ["筆次", "法院名稱", "字號(股別)", "拍賣日期拍賣次數", "縣市", "土地座落/面積", "總拍賣底價(元)", "點交", "空地", "標別", "備註", "採通訊投標", "土地有無遭受污染"]
        return seq_list[seq]

    def save_dict(self, list_info):
        dict_result = {"Result": list_info}
        with open("{}法拍{}.json".format(self.courtname(self.court), self.proptypename(self.proptype)), "w",
                  encoding="utf-8") as f:
            f.write(json.dumps(dict_result, ensure_ascii=False, indent=2))

    def run(self):  # 主要實現邏輯
        strfirsttrtd = ""
        strfirsttrtd_temp = ""
        dict_info2 = {}
        list_info2 = []
        # 頁面倍數
        pn = 1
        # 頁面起始筆數
        rowStart = 1
        # 設定總頁數
        pageTotal = 10
        break1, break2 = False, False
        page = 1
        # 1.構建url
        url_temp = self.url_page1.format(self.court, self.proptype)
        # 2.歷遍,發送請求,獲取響應
        while True:
            if page == 1:
                ret = self.parse_url(url_temp)
            else:
                strfirsttrtd = ""
                if page != 1:
                    print(self.url_nextpage.format(pageTotal, rowStart, self.court, self.proptype, page))
                    ret = self.parse_url(self.url_nextpage.format(pageTotal, rowStart, self.court, self.proptype, page))

            html = etree.HTML(ret)
            ret1 = html.xpath("//form[@name='form']/table[position()=1]//tr[position()>3]//table//tr[position()>1]")
            if len(ret1) == 0:
                break
            # print(len(ret1))
            # 3.取得數據
            # ret1 是 list
            ret1 = html.xpath("//form[@name='form']/table[position()=1]//tr[position()>3]//table//tr[position()>1]")
            # print(type(ret1))
            # print(len(ret1))  # 有15個tr list
            for i in ret1:
                ret2 = i.xpath("./td")
                for j in range(len(ret2)):
                    ret3 = ret2[j].xpath(".//text()")
                    if j == 5:
                        ret3_1 = ret2[j].xpath("./a/@href")[0]

                    strlast = ""
                    for k in range(len(ret3)):
                        str_temp = "".join(ret3[k].split())
                        if k == 0:
                            strstart = "".join(ret3[k].split())
                            strlast = strstart
                        else:
                            strlast = strlast + str_temp
                    print(strlast)
                    if strfirsttrtd == "":
                        strfirsttrtd = strlast
                        if strfirsttrtd != strfirsttrtd_temp:
                            strfirsttrtd_temp = strlast
                        else:
                            break1, break2 = True, True
                            break
                        print("=" * 10)

                    if strlast == "查詢":
                        ret4 = ret2[j].xpath("./a/@href")[0]
                        strlast = ret4
                        print(ret4)

                    if break2 == True:
                        break
                    else:
                        # 組合json
                        dict_str = self.combinejson(j)
                        dict_info2[dict_str] = strlast
                        if j == len(ret2) - 1:
                            dict_info2["pdf_info"] = ret3_1
                            list_info2.append(dict_info2)
                            dict_info2 = {}

                if break1 == True:
                    break
            if break1 == True:
                break

            page += 1
            if page % 10 == 1:
                pn += 1
                pageTotal += 10
                rowStart = 1 + (pn-1) * 150
        print(len(list_info2))
        # 4.保存
        self.save_dict(list_info2)


if __name__ == "__main__":
    lowhousespider = LowHouseSpider("TPD", "C51")
    lowhousespider.run()
