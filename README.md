# 데이터 분석 및 시각화

## remote repository clone 및 git pull
- github에서 repository 만들기(README.md, .gitignore 추가)
- local 컴퓨터에서 clone하기
```
git clone your_git_url data_analisys_ex
```

## uv 가상환경 만들기
```
uv init --bare --python 3.12 --name data_analisys
```

## 라이브러리 설치
```
uv add numpy pandas
uv add lxml
uv add matplotlib
uv add seaborn
uv add xlrd
uv add plotly
```

## ipykernel에 가상환경 추가하기
- ipykernel 설치
```
uv add ipykernel
```

- 가상환경 추가
```
uv run python -m ipykernel install --user --name .venv --display-name "eda_env"
```

## 시각화 한글 깨짐 문제해결 for WSL2 ubuntu
- matplotlib 한글 폰트 설치
```
sudo apt update
sudo apt install fonts-nanum
fc-list | grep Nanum

# 그래도 폰트가 계속 깨진다면 아래 명령어 실행하기 
rm -rf ~/.cache/matplotlib
```

- 파이썬 코드에서 적용
```
# 한글 폰트 설정
import platform

from matplotlib import rc
plt.rcParams['axes.unicode_minus'] = False

if platform.system() == 'Linux':
    rc('font', family = 'NanumGothic')  # 또는 '나눔고딕'
    print('Linux system... font set to NanumGothic')
elif platform.system() == 'Windows':
    rc('font', family = 'Malgun Gothic')   # 또는 '맑은 고딕'
    print('Windows system... font set to Malgun Gothic')
else:
    print('Unknown system... sorry~~~~')
```