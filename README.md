# Synthesizer_V_Gemini_helper
Synthesizer V 사용자의 보컬 작업 및 작곡 프로세스를 지원하기 위해 개발된 Gemini AI 기반 보조 도구입니다.

###  주요 기능 
* **신스븨 보이스 추천 :** gemini api를 활용하여 곡의 분위기에 맞는 캐릭터를 추천하고 그 이유를 말해 줍니다.
* **영어 입력시 신스븨 노트 발음 출력 :** 영어로 가사를 입력시 어떻게 노트에 넣어야 할지, 노트 분할 방법은 무엇이 있는지도 말해 줍니다.
* **한국어에 대응하는 영어 발음 출력 :** 한국어 가사를 입력하면 영문으로 번역되어 보다 수월하게 노래 작업을 할 수 있도록 돕습니다.
</br>

### 목차
1. [python 사용법](#python-사용법)
2. [exe & python 공통 사용법](#exe--python-공통-사용법)
3. [기능 소개 1](#1-신스븨-보이스-추천)
4. [기능 소개2](#2-영어-입력시-신스븨-노트-발음-출력)
5. [기능소개3](#3-한국어에-대응하는-영어-발음-출력)


- - -

 ### python 사용법
<br>
&nbsp;&nbsp;&nbsp;&nbsp;app.py 와 gemini_recomender.py 및 voices_data.py 는 한 폴더에 있어야 하며 실행하실파일은 app.py 입니다.
</br>
</br>
</br>
&nbsp;&nbsp;&nbsp;&nbsp;사용하시기 전에

> ```python
> pip install -U google-genai
> ```
&nbsp;&nbsp;&nbsp;&nbsp;다음 라이브러리들을 설치해 주셔야 사용이 가능합니다.
</br>
</br>
</br>


- - -
### exe & python 공통 사용법
<br>

&nbsp;&nbsp;&nbsp;&nbsp;0) [exe 파일](https://drive.google.com/drive/folders/1nb9UgU_VA1voSfAzWjLTpJLt74XGa4IJ?usp=sharing)을 사용하시는 분들 을 위한 파일입니다.
<br>
<br>
&nbsp;&nbsp;&nbsp;&nbsp;1)https://aistudio.google.com/api-keys 이 사이트에 들어가셔서 우측상단의 " api 키 만들기 " 를 클릭하여주십시오.
<br>
<br>
&nbsp;&nbsp;&nbsp;&nbsp;<img src="https://github.com/peropero1111/mp3_synthesizer_V_voice_mather-/blob/main/img/2026-06-23%20212257.png" width="450" height="450"/>  
<br>
<br>
&nbsp;&nbsp;&nbsp;&nbsp;2)  " API키 세부정보 " 라는 창이 뜨면 제일 위에 있는 API 키 를 복사 하여주십시오.
<br>
<br>
&nbsp;&nbsp;&nbsp;&nbsp;<img src="https://github.com/peropero1111/mp3_synthesizer_V_voice_mather-/blob/main/img/2026-06-23%20212349.png" width="450" height="450"/> 
<br>
<br>
&nbsp;&nbsp;&nbsp;&nbsp;3)  powershell 을 관리자 권한으로 열어주십시오.
</br>
</br>
&nbsp;&nbsp;&nbsp;&nbsp;<img src="https://github.com/peropero1111/mp3_synthesizer_V_voice_mather-/blob/main/img/2026-06-23%20211725.png" width="450" height="450"/>  
<br>
<br>
&nbsp;&nbsp;&nbsp;&nbsp;4)  관리자 권한으로열린 powershell 에 다음 명령어를 입력하여 주십시오.
</br>

>```bash
>[Environment]::SetEnvironmentVariable(
>  "GEMINI_API_KEY",
>  "당신의 API 키",
>  "User"
>)
>```
&nbsp;&nbsp;&nbsp;&nbsp;<img src="https://github.com/peropero1111/mp3_synthesizer_V_voice_mather-/blob/main/img/2026-06-23%20211831.png" width="450" height="450"/>  

</br>
</br>

- - -
## 기능 설명


### 1. 신스븨 보이스 추천 
<br>
&nbsp;&nbsp;&nbsp;&nbsp;위의 탭에서 <code>Synthesizer V 보이스 추천</code>을 누르신 후 자신이 가지고 있는 캐릭터를 선택하신 다음 .mp3 파일을 고르시면 그 .mp3 파일에 가장 잘 어울리는 캐릭터를 gemini 가 추천해 줍니다.
<br>
&nbsp;&nbsp;&nbsp;&nbsp;<img src="https://github.com/peropero1111/mp3_synthesizer_V_voice_matcher/blob/main/img/2026-08-05%20143524.png" width="450" height="450"/>  

---

### 2. 영어 입력시 신스븨 노트 발음 출력
<br>
&nbsp;&nbsp;&nbsp;&nbsp;위의 탭에서 <code>영어 입력하면 신스븨 발음 출력</code> 을 누르신 후 하단에 <code>영단어를</code> 입력하여 주시면 신스븨 에서 <code>가사에 들어갈 발음</code>, <code>노트 분할 힌트</code> (basic 버전) 등이 출력됩니다.
<br>
&nbsp;&nbsp;&nbsp;&nbsp;<img src="https://github.com/peropero1111/mp3_synthesizer_V_voice_matcher/blob/main/img/2026-08-05%20155948.png?raw=true" width="450" height="450"/>  

- - -

### 3. 한국어에 대응하는 영어 발음 출력
<br>
&nbsp;&nbsp;&nbsp;&nbsp;전에 Synthesizer V pro 에서는 한국어가 노트에 바로바로 입력되지 아니하여서 국립국어원 로마자표기법을 조금 변형한 게 있길래 적용하여서 만들어 보았습니다. 
<br>
<br>
&nbsp;&nbsp;&nbsp;&nbsp;마찬가지로 위의 탭에서 <code>한국어 입력하면 영어발음 출력</code>을 누르신 후에 한국어 단어/문장을 입력하시면 로마자 표기법에 맞게변환된 말이 나옵니다.
<br>
&nbsp;&nbsp;&nbsp;&nbsp;<img src="https://github.com/peropero1111/mp3_synthesizer_V_voice_matcher/blob/main/img/2026-08-05%20162406.png?raw=true" width="450" height="450"/>  
