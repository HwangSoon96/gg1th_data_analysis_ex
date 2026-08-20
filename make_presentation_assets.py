# -*- coding: utf-8 -*-
"""
발표용 차트 이미지 일괄 생성.
10번 노트북(데이터 분석 미니 프로젝트)의 분석을 재현해 presentation/images/ 에 PNG로 저장.
실행: .venv/bin/python make_presentation_assets.py
"""
import os, glob, json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon
from matplotlib.collections import PatchCollection
from matplotlib import rc, cm
import matplotlib.colors as mcolors

rc('font', family='NanumGothic')
plt.rcParams.update({
    'axes.unicode_minus': False,
    'font.size': 13, 'axes.titlesize': 16, 'axes.labelsize': 13,
    'xtick.labelsize': 11, 'ytick.labelsize': 11, 'legend.fontsize': 11,
    'figure.dpi': 150, 'savefig.bbox': 'tight',
})

OUT = 'presentation/images'
os.makedirs(OUT, exist_ok=True)
path = './data_pop'

def save(fig, name):
    p = f"{OUT}/{name}.png"
    fig.savefig(p)
    plt.close(fig)
    print("saved", p)

# ── 데이터 로드 ──
pop_files = sorted(glob.glob(f"{path}/*주민등록인구및세대현황*.csv"))
pop = pd.read_csv(pop_files[0], encoding="cp949", thousands=",").merge(
      pd.read_csv(pop_files[1], encoding="cp949", thousands=","), on="행정구역", how="outer")
age_files = sorted(glob.glob(f"{path}/*연령별인구현황*.csv"))
age = pd.read_csv(age_files[0], encoding="cp949", thousands=",")
for f in age_files[1:]:
    age = age.merge(pd.read_csv(f, encoding="cp949", thousands=","), on="행정구역", how="outer")
house = pd.read_csv(glob.glob(f"{path}/*세대원수별*.csv")[0], encoding="cp949", thousands=",")

def gu_name(s):
    s = s.split('(')[0].strip()
    return s.replace('경기도', '').replace('성남시', '').strip()

gus = ['수정구', '중원구', '분당구']
def pick_gu(df):
    d = df.copy(); d['지역'] = d['행정구역'].map(gu_name)
    return d[d['지역'].isin(gus)].set_index('지역')
pop_gu, age_gu, house_gu = pick_gu(pop), pick_gu(age), pick_gu(house)

# ── 1. 인구추이 ──
tot_cols = [c for c in pop.columns if '총인구수' in c]
인구추이 = pop_gu[tot_cols].T
인구추이.index = [c.split('년')[0] for c in 인구추이.index]
fig, ax = plt.subplots(figsize=(10, 5.5))
인구추이[['분당구','수정구','중원구']].plot(ax=ax, marker='o')
ax.set_title('성남시 3개 구 총인구 추이 (2008~2025)'); ax.set_ylabel('총인구수(명)'); ax.grid(alpha=0.3)
save(fig, '01_인구추이')

# ── 동별 함수 ──
def 구_동별(gu):
    d = age[age['행정구역'].str.contains(gu) & age['행정구역'].str.contains('동')].copy()
    d['동'] = d['행정구역'].map(lambda s: s.split('(')[0].split(gu)[-1].strip())
    d = d.dropna(subset=['2016년_계_총인구수'])
    d['2016'] = d['2016년_계_총인구수'].astype(int)
    d['2025'] = d['2025년_계_총인구수'].astype(int)
    d['증감'] = d['2025'] - d['2016']
    return d[['동','2016','2025','증감']].sort_values('증감', ascending=False).reset_index(drop=True)
수정_동별, 중원_동별 = 구_동별('수정구'), 구_동별('중원구')

# ── 2. 수정구 동별 증감 ──
fig, ax = plt.subplots(figsize=(8.5, 7))
c = ['#d62728' if v > 0 else '#1f77b4' for v in 수정_동별['증감']]
수정_동별.set_index('동')['증감'].plot(kind='barh', ax=ax, color=c)
ax.set_title('수정구 동별 인구 증감 (2016~2025)'); ax.set_xlabel('증감(명)')
ax.axvline(0, color='k', lw=0.8); ax.invert_yaxis()
save(fig, '02_수정구_동별증감')

# ── 4. 중원구 동별 증감 ──
fig, ax = plt.subplots(figsize=(8.5, 6))
c = ['#d62728' if v > 0 else '#1f77b4' for v in 중원_동별['증감']]
중원_동별.set_index('동')['증감'].plot(kind='barh', ax=ax, color=c)
ax.set_title('중원구 동별 인구 증감 (2016~2025)'); ax.set_xlabel('증감(명)')
ax.axvline(0, color='k', lw=0.8); ax.invert_yaxis()
save(fig, '04_중원구_동별증감')

# ── 3. 신규 vs 원도심 비교 ──
def 신구_분해(gu, 신규):
    d = 구_동별(gu)
    return pd.Series({'신규택지 동': d[d['동'].isin(신규)]['증감'].sum(),
                      '원도심 동': d[~d['동'].isin(신규)]['증감'].sum(),
                      '구 전체': d['증감'].sum()})
비교 = pd.DataFrame({'수정구': 신구_분해('수정구', ['위례동','고등동','신흥2동']),
                   '중원구': 신구_분해('중원구', ['금광1동'])})
fig, ax = plt.subplots(figsize=(9, 5.5))
비교.T.plot(kind='bar', ax=ax, color=['#2ca02c','#1f77b4','#7f7f7f'])
ax.set_title('신규택지 vs 원도심 인구 증감 (2016→2025)'); ax.set_ylabel('증감(명)')
ax.axhline(0, color='k', lw=0.8); ax.tick_params(axis='x', rotation=0)
save(fig, '03_신규vs원도심_비교')

# ── 연령비율 ──
years = [c.split('년')[0] for c in age.columns if c.endswith('년_계_총인구수')]
def 연령비율(bands):
    out = {}
    for y in years:
        tot = age_gu[f'{y}년_계_총인구수']
        out[y] = sum(age_gu[f'{y}년_계_{b}'] for b in bands) / tot * 100
    return pd.DataFrame(out).T
elderly = ['60~69세','70~79세','80~89세','90~99세','100세 이상']

# ── 5. 60세+ 비율 추이 ──
고령비율 = 연령비율(elderly)
fig, ax = plt.subplots(figsize=(10, 5.5))
고령비율[['분당구','수정구','중원구']].plot(ax=ax, marker='o')
ax.set_title('60세 이상 인구 비율 추이 (%)'); ax.set_ylabel('비율(%)'); ax.grid(alpha=0.3)
save(fig, '05_60세이상_비율추이')

# ── 6. 아동 수 ──
아이수 = pd.DataFrame({y: age_gu[f'{y}년_계_0~9세'] for y in ['2008','2025']}).astype(int)
fig, ax = plt.subplots(figsize=(8, 5.5))
아이수.loc[['분당구','수정구','중원구']].plot(kind='bar', ax=ax, color=['#aec7e8','#d62728'])
ax.set_title('0~9세 아동 수 변화 (2008 → 2025)'); ax.set_ylabel('아동 수(명)'); ax.tick_params(axis='x', rotation=0)
for i, 지역 in enumerate(['분당구','수정구','중원구']):
    dec = (아이수.loc[지역,'2025'] - 아이수.loc[지역,'2008']) / 아이수.loc[지역,'2008'] * 100
    ax.annotate(f'{dec:.0f}%', (i, 아이수.loc[지역,'2025']), ha='center', va='bottom', color='#d62728')
ax.legend(title='연도')
save(fig, '06_아동수_변화')

# ── 7. 세대당 인구 추이 ──
세대당_cols = [c for c in pop.columns if '세대당 인구' in c]
세대당 = pop_gu[세대당_cols].T
세대당.index = [c.split('년')[0] for c in 세대당.index]
fig, ax = plt.subplots(figsize=(10, 5.5))
세대당[['분당구','수정구','중원구']].plot(ax=ax, marker='o')
ax.set_title('세대당 인구 추이 (명/세대)'); ax.set_ylabel('세대당 인구(명)')
ax.axhline(2.0, color='gray', ls='--', alpha=0.5); ax.grid(alpha=0.3)
save(fig, '07_세대당인구_추이')

# ── 8. 1인세대 비율 추이 ──
hyears = [c.split('년')[0] for c in house.columns if '전체세대' in c]
def hcol(y, key): return [c for c in house.columns if c.startswith(y) and key in c][0]
one = {y: house_gu[hcol(y,'1인세대')] / house_gu[hcol(y,'전체세대')] * 100 for y in hyears}
일인 = pd.DataFrame(one).T
fig, ax = plt.subplots(figsize=(10, 5.5))
일인[['수정구','중원구','분당구']].plot(ax=ax, marker='o', color=['#d62728','#ff7f0e','#1f77b4'])
ax.set_title('1인 세대 비율 추이 (%)'); ax.set_ylabel('비율(%)'); ax.grid(alpha=0.3)
save(fig, '08_1인세대_추이')

# ── 9. 세대원수 구성 ──
t = house_gu[hcol('2025','전체세대')]; s1 = house_gu[hcol('2025','1인세대')]; s2 = house_gu[hcol('2025','2인세대')]
세대구성 = pd.DataFrame({'1인': s1/t*100, '2인': s2/t*100, '3인+': (t-s1-s2)/t*100}).loc[['수정구','중원구','분당구']]
fig, ax = plt.subplots(figsize=(8, 5.5))
세대구성.plot(kind='bar', stacked=True, ax=ax, color=['#d62728','#ff7f0e','#1f77b4'])
ax.set_title('세대원수 구성비 (2025)'); ax.set_ylabel('비율(%)'); ax.tick_params(axis='x', rotation=0); ax.legend(title='세대원수')
save(fig, '09_세대원수_구성')

# ── 10. 동 유형별 연령 프로필 ──
신규택지동 = ['위례동','고등동','신흥2동','금광1동']
def 동_모으기(gu):
    d = age[age['행정구역'].str.contains(gu) & age['행정구역'].str.contains('동')].copy()
    d['동'] = d['행정구역'].map(lambda s: s.split('(')[0].split(gu)[-1].strip())
    return d
후보 = pd.concat([동_모으기('수정구'), 동_모으기('중원구')])
후보['유형'] = 후보['동'].map(lambda x: '신규택지' if x in 신규택지동 else '원도심')
def 프로필(df):
    tot = df['2025년_계_총인구수'].sum()
    e = sum(df[f'2025년_계_{b}'] for b in elderly).sum(); k = df['2025년_계_0~9세'].sum()
    return pd.Series({'60세+ %': e/tot*100, '0~9세 %': k/tot*100})
프로필표 = pd.DataFrame({
    '신규 입주지(2010s)': 프로필(후보[후보['유형']=='신규택지']),
    '분당(1990s)': 프로필(age[age['행정구역'].map(gu_name)=='분당구']),
    '원도심': 프로필(후보[후보['유형']=='원도심']),
}).T
fig, ax = plt.subplots(figsize=(8.5, 5.5))
프로필표.plot(kind='bar', ax=ax, color=['#d62728','#2ca02c'])
ax.set_title('입주 시기별 연령 프로필 (2025)'); ax.set_ylabel('비율(%)'); ax.tick_params(axis='x', rotation=0)
for cont in ax.containers:
    ax.bar_label(cont, fmt='%.1f', fontsize=9)
save(fig, '10_동유형_연령프로필')

# ── 11. 분당 연령 구성 변화 ──
bands = ['0~9세','10~19세','20~29세','30~39세','40~49세','50~59세','60~69세','70~79세','80~89세','90~99세','100세 이상']
분당 = age[age['행정구역'].map(gu_name)=='분당구']
def bshare(y):
    tot = 분당[f'{y}년_계_총인구수'].sum()
    return pd.Series({b: 분당[f'{y}년_계_{b}'].sum()/tot*100 for b in bands})
분당연령 = pd.DataFrame({'2008': bshare('2008'), '2025': bshare('2025')})
fig, ax = plt.subplots(figsize=(11, 5.5))
분당연령.plot(kind='bar', ax=ax, color=['#aec7e8','#d62728'])
ax.set_title('분당구 연령대 구성 변화 (2008 → 2025)'); ax.set_ylabel('비율(%)'); ax.tick_params(axis='x', rotation=45)
save(fig, '11_분당_연령구성변화')

# ── 12. 동별 인구 지도 (정적, geojson 폴리곤 직접 렌더) ──
geo = json.load(open('map_data/seongnam_admdong.geojson', encoding='utf-8'))
동인구 = {}
_d = age[age['행정구역'].str.contains('성남시') & age['행정구역'].str.contains('동')]
for _, r in _d.iterrows():
    if pd.isna(r['2025년_계_총인구수']): continue
    nm = r['행정구역'].split('(')[0].split()
    동인구[(nm[-2], nm[-1])] = int(r['2025년_계_총인구수'])

def rings(geom):
    if geom['type'] == 'Polygon': return [geom['coordinates'][0]]
    return [poly[0] for poly in geom['coordinates']]

vals = []
for f in geo['features']:
    parts = f['properties']['adm_nm'].split()
    gu, dong = parts[1].replace('성남시',''), parts[-1]
    f['properties']['_pop'] = 동인구.get((gu, dong), 0)
    f['properties']['_dong'] = dong
    if f['properties']['_pop'] > 0: vals.append(f['properties']['_pop'])
norm = mcolors.Normalize(vmin=min(vals), vmax=max(vals))
cmap = plt.get_cmap('YlOrRd')

fig, ax = plt.subplots(figsize=(9, 10))
for f in geo['features']:
    color = cmap(norm(f['properties']['_pop'])) if f['properties']['_pop'] else '#dddddd'
    xs_all, ys_all = [], []
    for ring in rings(f['geometry']):
        poly = MplPolygon(ring, closed=True, facecolor=color, edgecolor='white', linewidth=0.6)
        ax.add_patch(poly)
        xs_all += [p[0] for p in ring]; ys_all += [p[1] for p in ring]
    cx, cy = np.mean(xs_all), np.mean(ys_all)
    ax.annotate(f['properties']['_dong'], (cx, cy), ha='center', va='center', fontsize=6.5, color='#222')
ax.autoscale(); ax.set_aspect('equal'); ax.axis('off')
ax.set_title('성남시 동별 총인구 (2025)', fontsize=16)
sm = cm.ScalarMappable(norm=norm, cmap=cmap); sm.set_array([])
fig.colorbar(sm, ax=ax, shrink=0.5, label='총인구(명)')
save(fig, '12_동별인구_지도')

print("\n완료: presentation/images/ 에 이미지 저장")
