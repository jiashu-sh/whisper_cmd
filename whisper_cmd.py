import sys
import wave
import pyaudio
import time
import datetime
import random
# 配置文件的包
import configparser
# 使用pynput捕捉键盘鼠标事件hook
from pynput import keyboard
# 微软翻译的包
import requests, uuid, json

import whisper
from zhconv import convert # 中文简繁体转换

# import pyperclip
import pyperclip as pc

from bs4 import BeautifulSoup
import requests

import tkinter

import jieba

#region 录音参数设定（全局）
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
MAX_READ_SECONDS = 28 #理论最大30s，保险起见减少2s
WAVE_OUTPUT_FILENAME = "./rec/rec.wav"
#endregion

IsEsc = False
IsRec = False
ListenerStarted = False
# 优化：将语音解析模型导入到全局
print("loadint whisper model ...")
t_clock_loading_model = time.time()
# load_model 若指定了download_root参数，os.path.join(os.getenv("XDG_CACHE_HOME", default), "whisper") 即从指定目录获取模型，默认是 print(os.path.expanduser("~"))获取C:\Users\用户的文件夹下 join ".cache" 目录 join whisper 目录下 base.pt medium.pt small.pt等模型
model = whisper.load_model("medium") # 增加参数 ,"cpu",None,True 好像还是有错误 def load_model(name: str, device: Optional[Union[str, torch.device]] = None, download_root: str = None, in_memory: bool = False) 
t_rec = round((time.time() - t_clock_loading_model),2)
print("load whisper model elapsed {0} sec".format(t_rec))

#region 类转换示例
"""
class TranslateContent(object):
    def __init__(self, text: str, to: str):
        self.text = text
        self.to = to
    
def json_to_translate(translateContent: dict) -> TranslateContent:
    translateContent = TranslateContent(
        text=translateContent['text'],
        to=translateContent['to']
    )
    return translateContent

# 示例
# 预处理
trans_str= response.strip('[]').strip('{}').replace("'translations'","").strip().strip(':').strip().strip('[]')
trans_str = trans_return.replace("''","\"")

s2= "{\"text\": \"Today unstained reaction\", \"to\": \"en\"}"
r = json_to_translate(json.loads(s2))  

"""
#endregion

#调用微软翻译中翻英
def translate_ms(transText,langFrom="zh-Hans",langTo="en",IsDebug = False):
    trans_return = ""
    # 读取ini配置文件
    cf=configparser.ConfigParser()   #创建对象
    cf.read('./config.ini',encoding='UTF-8') 
    # lstCfg = cf.items("TranslatorConf")
    config_key = cf.get('TranslatorConf','key')
    config_region = cf.get('TranslatorConf','location')
    
    # Add your key and endpoint # API访问端点
    key = config_key #"<your-translator-key>"
    endpoint = "https://api.cognitive.microsofttranslator.com" #"https://api.cognitive.microsofttranslator.com"

    # location, also known as region.
    # required if you're using a multi-service or regional (not global) resource. It can be found in the Azure portal on the Keys and Endpoint page.
    location = config_region # "<YOUR-RESOURCE-LOCATION>"

    path = '/translate' # Api访问路径。
    constructed_url = endpoint + path #使用方法：API访问端点+Api访问路径

    params = {
        'api-version': '3.0',
        'from': langFrom, # 从英文翻译
        'to': [langTo] # ['zh-Hans', 'ja'] # 翻译到中文简体，日文（可支持多个）
    }

    headers = {
        'Ocp-Apim-Subscription-Key': key,
        # location required if you're using a multi-service or regional (not global) resource.
        'Ocp-Apim-Subscription-Region': location,
        'Content-type': 'application/json',
        'X-ClientTraceId': str(uuid.uuid4())
    }

    # You can pass more than one object in body.# 要翻译的文本
    body = [{
        'text': transText
    }]

    request = requests.post(constructed_url, params=params, headers=headers, json=body)
    response = request.json()
    # print(json.dumps(response, sort_keys=True, indent=4, separators=(',', ': ')))

    # s.index("'translations'")
    if ( len(response) >0 ) :
        trans_return = response[0]["translations"][0]["text"]
    
    return trans_return

#调用有道翻译中翻英
def translate(data,IsDebug = False):
    trans_return = ""
    # data = input("请输入翻译的词语\n")
    # if data is '':
    #     print("输入有误,请重新输入")
    #     translate()
    print("翻译："+ data)
    if IsDebug:
        print("翻译："+ data)
    if data == "":
        return trans_return
    web_data = requests.get('https://www.youdao.com/result?word={}&lang=en'.format(data))
    Soup = BeautifulSoup(web_data.content, 'lxml')
    result = Soup.findAll('div', attrs={'class': 'trans-container'})
    
    data = result[0:2]
    # print(str(data))
    for div in data:
        # print(str(div))
        childs = BeautifulSoup(str(div), 'lxml')
        dtls = childs.findAll('a', attrs={'class': 'point'})
        for d in dtls:
            # print(str(d))
            if IsDebug:
                print(d.get_text())
            trans_return = d.get_text()
            break
        # print(i.get_text())
    
    return trans_return

def on_press(key,IsDebug = False):
    try:
        if IsDebug:
            print("key: {0} pressed".format(key.char))
    except AttributeError:
        if IsDebug:
            print("special key {0} pressed".format(key))
    if key == keyboard.Key.f9: # 按下F6键执行改IsRec是否录音状态
        global IsRec
        IsRec = not IsRec
        print("rec status :{0}".format(str(IsRec)))
        # return False

def on_release(key,IsDebug = False):
    # try:
    #     print("key: {0} released".format(key.char))
    # except AttributeError:
    #     print("special key {0} released".format(key))
    if IsDebug:
        print("key: {0} released".format(key))
    if key== keyboard.Key.esc: # stop listener # 按下esc键修改IsEsc 标记 退出while循环
        global IsEsc
        IsEsc = True
        print("exit :{0}".format(str(IsEsc)))
        return False
    
def press_ctrl_v():
    '''
    测试Ctrl_v效果的代码
    time.sleep(1.5)
    pc.copy("测试机哈哈哈啊啊 : "+ datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
    time.sleep(0.5)
    pc.paste() # 不知为何黏贴没效果，本来的想法是自动复制黏贴到当前窗体
    # pc.paste() # 不知为何黏贴没效果，本来的想法是自动复制黏贴到当前窗体 - 正确用法应该是 str=pc.paste()，粘贴到字符串
    '''
    control = keyboard.Controller()
    control.press(keyboard.Key.ctrl)
    control.press(keyboard.KeyCode.from_char("v"))
    control.release(keyboard.KeyCode.from_char("v"))
    control.release(keyboard.Key.ctrl)

def speechToText(fileName,IsDebug = False) :
    # 语音转文本方法
    # 将model放入全局，避免每次都重新加载
    # model = whisper.load_model("medium") # model = whisper.load_model("medium") base
    global model
    # load audio and pad/trim it to fit 30 seconds
    # N_SAMPLES = CHUNK_LENGTH * SAMPLE_RATE  # 480000 samples in a 30-second chunk
    N_SAMPLES = 480000
    audio = whisper.load_audio(fileName)
    audio = whisper.pad_or_trim(audio) # 若过长的音频，超过30s需要截断
    # print(type(audio))
    # print(len(audio))

    t_clock = time.time()
    # make log-Mel spectrogram and move to the same device as the model
    mel = whisper.log_mel_spectrogram(audio).to(model.device) #显存不够用cpu： mel = whisper.log_mel_spectrogram(audio).to("cpu") model.device 
    # parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu", help="device to use for PyTorch inference")
    
    # options = whisper.DecodingOptions() 

    # detect the spoken language # 检测音源
    _, probs = model.detect_language(mel)
    if IsDebug:
        print(f"Detected language: {max(probs, key=probs.get)}")

    # decode the audio
    # 是否启用半精度 fp16 进行推理运算，默认为 True，否则为单精度 fp32，运行时间延长。
    options = whisper.DecodingOptions() #options = whisper.DecodingOptions(fp16 = False) 
    result = whisper.decode(model, mel, options)
    
    # 输出耗时
    t_rec = round((time.time() - t_clock),2)
    print("elapsed {0} sec".format(t_rec))
    
    # 转换为简体中文
    zh_result = convert(str(result.text),"zh-cn") #"zh-hant"繁体 zh-cn 大陆简体
    if IsDebug:
        print(result.text)
    return(zh_result)

def isChinese(ch):
        if '\u4e00' <= ch <= '\u9fff':
            return True
        return False
    
def isEnglish(ch):
    if (u'\u0041' <= ch <= u'\u005a') or (u'\u0061' <= ch <= u'\u007a'):
        return True
    return False
    
def isNumber(ch):
    if u'\u0030' <= ch <= u'\u0039':
        return True
    return False

def showContentWindow(sttContent,sContent=""):
    # 弹出录音内容窗口
    # 定义一个窗体
    mainwin = tkinter.Tk()
    mainwin.attributes("-alpha",1.0)
    mainwin.title("STT content")
    winWidth = 480
    winHeight = 250
    mainwin.geometry(
        f"{str(winWidth)}x{str(winHeight)}+"+
        f"{int((mainwin.winfo_screenwidth() - winWidth)/2)}+"+
        f"{int((mainwin.winfo_screenheight() - winHeight)/2)}"
    )
    
    # style = tkinter.ttk.Style()
    # style.configure( 'TButton' , font = 
    #             ( 'calibri' , 20 , 'bold' ), borderwidth = '4' )
    
    # 设置容器
    frame1 = tkinter.Frame(mainwin,height=110,width=200,relief=tkinter.GROOVE, bg='#FFFAF0',bd=1,borderwidth=1)
    # 设置填充和布局
    frame1.pack(fill=tkinter.BOTH,ipady=0,expand=True,side=tkinter.TOP)
    frame1.pack_propagate(False)
    # 设置容器
    frame2 = tkinter.Frame(mainwin,height=110,width=200,relief=tkinter.GROOVE, bg='#CCFFCC',bd=1,borderwidth=1)
    # 设置填充和布局
    frame2.pack(fill=tkinter.BOTH,ipady=0,expand=True,side=tkinter.TOP)
    frame2.pack_propagate(False)
    # 设置容器
    frame3 = tkinter.Frame(mainwin,height=30,width=200,relief=tkinter.GROOVE, bg='#CCCCCC',bd=1,borderwidth=1)
    # 设置填充和布局
    frame3.pack(fill=tkinter.X,ipady=0,expand=False,side=tkinter.BOTTOM)
    frame3.pack_propagate(False)
    
    txt_content = sttContent
    # 设置两个文本框， grid是设置页面位置
    text_content = tkinter.Text(frame1,width=50,height=100, font=("宋体", 12, "normal"),bg='#FFFAF0') #, tkinter.Entry(show='',  bg='white', highlightcolor='blue', relief='raised',width=60,textvariable=txt_content）
    text_content.pack(fill=tkinter.X,expand=False,side=tkinter.TOP,anchor=tkinter.N)
    text_content.insert("insert",txt_content)
    text_content.focus_set()
    
    txt_splited_content = sContent
    text_content_split = tkinter.Text(frame2,width=50,height=100, font=("宋体", 12, "normal"),bg='#CCFFCC') #, tkinter.Entry(show='',  bg='white', highlightcolor='blue', relief='raised',width=60,textvariable=txt_content）
    text_content_split.pack(fill=tkinter.X,expand=False,side=tkinter.TOP,anchor=tkinter.N)
    text_content_split.insert("insert",txt_splited_content)
    # text_content_split.focus_set()
    
    
    
    def sendStr():
        # txt_get = text_content_split.get("1.0","end")
        # pc.copy(str(txt_get))
        # print('Data Send Ok!')
        txt_get = text_content.get("1.0","end")
        ch = random.choice(txt_get) # 从字符串中随机取一个字符
        if isNumber(ch): # 若为数字再随机取一个
            ch = random.choice(txt_get)
        language1 = cf.get('TranslatorConf','language1')
        language2 = cf.get('TranslatorConf','language2')
        langFrom = language1
        langTo = language2
        if not isChinese(ch):
            langFrom = language2
            langTo = language1
        if bTranslate: #若需要翻译  则增加开关 translate:true
            text_trans = translate_ms(str(txt_get),langFrom,langTo)
            text_content_split.delete("1.0","end")
            text_content_split.insert("insert",text_trans)
        
        
    button1 = tkinter.Button(frame3,text='Translate'+'\n' + '(redo-tranlate)', width=90,height=2,font=("Arial,宋体", 9, "normal"),command=sendStr)
    # button1.config()
    button1.pack(expand=True)
    
    # 将其加入主循环
    mainwin.mainloop()
    # print(txt_get)
    # exit()


if __name__ == "__main__" :
    
    # 读取ini配置文件
    cf=configparser.ConfigParser()   #创建对象
    cf.read('./config.ini',encoding='UTF-8') 
    # lstCfg = cf.items("TranslatorConf")
    print(cf.get('TranslatorConf','key'))
    print(cf.get('TranslatorConf','location'))
    print(cf.get('TranslatorConf','language1'))
    print(cf.get('TranslatorConf','language2'))

    # python whisper_cmd.py showin:true    -- 使用这个启动，弹出窗口
    # python whisper_cmd.py                 -- 不带参数，默认不弹出窗口，直接把语音内容复制到剪贴板，并粘贴到当前窗口（不翻译）
    
    bTranslate = False # 是否自动翻译
    bShowContentWindow = False # 是否弹出窗口

    #region 测试代码
    # 测试弹出窗口 测试结巴分词
    # showContentWindow("1","2")
    # exit()
    
    # t1="在精确模式的基础上，对发现的那些长的词语，我们会对它再次切分，进而适合搜索引擎对短词语的索引和搜索。也有冗余。有一副画，哥特式样风格建筑群，哥特式教堂，赛博朋克的光环闪耀。"
    # splited_txt = []
    # if len(t1) > 0:
    #     #-- splited_txt = jieba.lcut(t1,cut_all = True)
    #     #-- print(splited_txt)
    #     seg_list = jieba.cut(t1)  # 默认是精确模式
    #     print(seg_list)
    #     print("默认模式: " + "/ ".join(seg_list))
    #     #-- jieba.analyse.textrank(t1, topK=20, withWeight=False, allowPOS=('ns', 'n', 'vn', 'v'))  # 有默认词性
    #     #-- jieba.analyse.TextRank()  # 新建自定义 TextRank 实例
    # exit()
    #endregion
    
    #region 解析命令行参数
    cmdPara1 = ""
    if (len(sys.argv) > 1) :
        cmdPara1 = str(sys.argv[1])
        for idxPara in range(len(sys.argv)) :
            sPara = sys.argv[idxPara]
            print(sPara)
            if sPara == "translate:on" :
                bTranslate = True
            elif sPara == "translate:off" :
                bTranslate = False
            elif sPara == "showin:on" :
                bShowContentWindow = True
            elif sPara == "showin:off" :
                bShowContentWindow = False
    #endregion

    print("* press F9 to start/stop recording... (esc to exit)")
    
    # in a non-blocking fashion: #开启后等待停止
    listener = keyboard.Listener(on_press=on_press,on_release= on_release)
    listener.start()
    
    i_count = 0
    while (not IsEsc) :
        #region 读取按键模式:示例代码
        # Collect events until released # 独占模式
        # with keyboard.Listener(on_press=on_press,on_release= on_release) as listener:
        #     listener.join()
        #endregion

        # 开始录音：设置时间戳文件名，并输入提示信息
        if IsRec: 
            s_dt_now = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            WAVE_OUTPUT_FILENAME = "./rec/rec-{0}.wav".format(s_dt_now)
            print("start rec ...（{0}）".format(s_dt_now) + " . file{0}".format(WAVE_OUTPUT_FILENAME))
        # else :
        #     print("end rec.")
        '''
        开始处理：按下F9后
        ''' 
        if IsRec : 
            #region 录音wav文件存入缓存目录
            # 开始录音30s以内，实际上定义的MAX_READ_SECONDS是28s-------------------
            audio_device = pyaudio.PyAudio() 
            stream = audio_device.open(format=FORMAT,channels=CHANNELS,rate=RATE,input=True,frames_per_buffer=CHUNK)
            t_clock = time.time()
            t_rec = 0
            frames = []
            j_rec_status = 0
            for i in range(0,int(RATE / CHUNK * MAX_READ_SECONDS)):
                data=stream.read(CHUNK)
                frames.append(data)
                if (j_rec_status % 20) == 0 : # 每5次循环打印一个录音标记*
                    print("*",end='') #不换行
                if not IsRec:
                    t_rec = round((time.time() - t_clock),2)
                    break
                j_rec_status += 1
            
            stream.stop_stream()
            stream.close()

            audio_device.terminate()
            # -------------------------------------------------------------------
            #endregion

            # 录音提交stt解析-------------------------------------
            wf = wave.open(WAVE_OUTPUT_FILENAME,"wb")
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(audio_device.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(frames))
            wf.close()
            
            print("rec end, elapsed {0} sec".format(t_rec))
            
            txt = speechToText(WAVE_OUTPUT_FILENAME)
            # ---------------------------------------------------
            
            print(txt)
            
            if bTranslate: #若需要翻译  则增加开关 translate:true
                str_en = translate_ms(str(txt))
                print(str_en)
                
            splited_txt = []
            if len(txt) > 0:
                splited_txt = jieba.lcut(txt,cut_all = True)
                seg_list = jieba.cut(txt)
                seg_txt = "" + "/ ".join(seg_list) 
            if bShowContentWindow : # 弹出窗口 str_en
                showContentWindow(txt,str_en) # showContentWindow(txt,seg_txt)
            else : # 进行拷贝粘贴
                pc.copy(str(txt))
                press_ctrl_v()
            
        i_count += 1
        time.sleep(0.2)
        if (i_count % 25) == 0 :
            print(".",end='') #不换行
        # print(IsEsc)
        
        
    exit()


''''''
