# PROB-03 数字特征、大数定律与中心极限定理

## 一、数学期望

期望是随机变量取值的"加权平均"，反映了随机变量的集中趋势。

**离散型**：E(X)=Σxi·pi（每个取值乘以其概率后求和）
**连续型**：E(X)=∫x·f(x)dx（x乘以密度函数的积分）

**期望的性质**：
1. E(c)=c（常数）
2. E(aX+b)=aE(X)+b（线性变换）
3. E(X±Y)=E(X)±E(Y)（线性可加性，不需要独立）
4. 如果X与Y独立，则E(XY)=E(X)E(Y)

## 二、方差

方差衡量随机变量取值偏离期望的程度。方差越大，数据越分散。

D(X)=E[(X-E(X))²]=E(X²)-[E(X)]²

**方差的性质**：
1. D(c)=0
2. D(aX+b)=a²D(X)
3. 如果X与Y独立，则D(X±Y)=D(X)+D(Y)

## 三、协方差与相关系数

协方差Cov(X,Y)=E[(X-E(X))(Y-E(Y))]=E(XY)-E(X)E(Y)

相关系数ρXY=Cov(X,Y)/√(D(X)D(Y))

相关系数ρ的取值范围是[-1,1]，它衡量了X与Y之间的线性相关程度：
- ρ=0：X与Y不相关（但注意：不相关不等于独立，只是没有线性关系）
- |ρ|=1：X与Y完全线性相关
- X与Y独立⇒ρ=0（独立一定不相关），但逆命题不成立，除非(X,Y)服从二维正态分布

## 四、切比雪夫不等式

P{|X-μ|≥ε}≤σ²/ε²

这个不等式不需要知道X的具体分布，只需要知道期望和方差，就能对X偏离期望的概率给出一个上界估计。

**例**：设E(X)=μ，D(X)=σ²，用切比雪夫不等式估计P{|X-μ|<3σ}。

> P{|X-μ|<3σ} ≥ 1 - σ²/(3σ)² = 1 - 1/9 = 8/9
> 即任何随机变量，其值落在均值附近三倍标准差范围内的概率至少为8/9。

## 五、中心极限定理

中心极限定理是概率论中最重要的定理之一。它指出：大量独立同分布的随机变量之和（或均值）近似服从正态分布，无论这些随机变量本身的分布是什么。

设X₁,...,Xn独立同分布，E(Xi)=μ，D(Xi)=σ²，则当n充分大时：
Sn=X₁+...+Xn ~ N(nμ, nσ²) 近似成立

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 560 130" width="100%" height="130">
  <text x="10" y="16" font-size="11" font-weight="bold" fill="#1565c0">中心极限定理示意图：不同分布 → 正态分布</text>
  <rect x="10" y="25" rx="4" ry="4" width="75" height="50" fill="#e3f2fd" stroke="#1976d2" stroke-width="1.5"/>
  <text x="47" y="42" text-anchor="middle" font-size="9" fill="#1565c0">均匀分布</text>
  <rect x="14" y="48" width="20" height="15" fill="#90caf9" stroke="none"/><rect x="36" y="48" width="20" height="18" fill="#90caf9" stroke="none"/><rect x="58" y="48" width="20" height="15" fill="#90caf9" stroke="none"/>
  <line x1="100" y1="50" x2="125" y2="50" stroke="#999" stroke-width="1.5" marker-end="url(#cl)"/>

  <rect x="130" y="25" rx="4" ry="4" width="75" height="50" fill="#fff3e0" stroke="#e65100" stroke-width="1.5"/>
  <text x="167" y="42" text-anchor="middle" font-size="9" fill="#e65100">指数分布</text>
  <polygon points="138,68 138,48 155,50 170,55 185,60 197,68" fill="rgba(230,81,0,0.3)" stroke="#e65100" stroke-width="1" fill-opacity="0.5"/>
  <line x1="220" y1="50" x2="245" y2="50" stroke="#999" stroke-width="1.5" marker-end="url(#cl)"/>

  <rect x="250" y="25" rx="4" ry="4" width="75" height="50" fill="#e8f5e9" stroke="#43a047" stroke-width="1.5"/>
  <text x="287" y="42" text-anchor="middle" font-size="9" fill="#2e7d32">二项分布</text>
  <rect x="260" y="52" width="8" height="18" fill="#a5d6a7" stroke="none"/><rect x="272" y="58" width="8" height="12" fill="#a5d6a7" stroke="none"/><rect x="284" y="50" width="8" height="20" fill="#a5d6a7" stroke="none"/><rect x="296" y="55" width="8" height="15" fill="#a5d6a7" stroke="none"/><rect x="308" y="60" width="8" height="10" fill="#a5d6a7" stroke="none"/>
  <line x1="340" y1="50" x2="365" y2="50" stroke="#999" stroke-width="1.5" marker-end="url(#cl)"/>

  <text x="410" y="42" text-anchor="middle" font-size="10" fill="#7b1fa2" font-weight="bold">→ n→∞</text>
  <path d="M 375 70 Q 390 25 410 50 Q 430 70 450 50 Q 470 25 485 50 Q 500 70 510 55" fill="none" stroke="#7b1fa2" stroke-width="2"/>
  <text x="445" y="85" text-anchor="middle" font-size="9" fill="#7b1fa2">N(μ, σ²/n)</text>
  <text x="445" y="100" text-anchor="middle" font-size="8" fill="#555">近似正态分布</text>
  <defs><marker id="cl" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5" markerHeight="5" orient="auto"><path d="M 0 0 L 10 5 L 0 10 z" fill="#999"/></marker></defs>
</svg>

中心极限定理解释了为什么正态分布在自然界和工程中如此常见——许多随机现象可以视为大量独立随机因素的总和。

**保险公司盈利问题（2024真题）**：500辆车，每辆事故概率0.006，保费800元，赔偿50000元，求赚钱≥200000元的概率。

> 每辆车的盈利Xi：
> 不出事（概率0.994）：盈利800元
> 出事（概率0.006）：盈利800-50000=-49200元
> E(Xi)=800×0.994+(-49200)×0.006=500
> D(Xi)=E(Xi²)-500²
> E(Xi²)=800²×0.994+(-49200)²×0.006≈14,901,200
> D(Xi)≈14,901,200-250,000=14,651,200
>
> 总盈利S=ΣXi，E(S)=500×500=250,000
> D(S)=500×14,651,200=7,325,600,000，σ(S)≈85,592
> P{S≥200,000}=P{Z≥(200,000-250,000)/85,592}
> =P{Z≥-0.584}=Φ(0.584)≈0.720
>
> 保险公司有约72%的概率盈利不低于20万元。
