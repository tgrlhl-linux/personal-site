# PROB-01 概率论基础

## 一、古典概型

古典概型是最简单的概率模型。它要求试验满足两个条件：样本空间只有有限个样本点，且每个样本点出现的可能性相同。在古典概型下，事件A的概率定义为：

P(A) = A包含的样本点数 / 样本空间的总样本点数

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 130" width="100%" height="130">
  <ellipse cx="110" cy="60" rx="70" ry="50" fill="rgba(25,118,210,0.12)" stroke="#1976d2" stroke-width="2"/>
  <ellipse cx="200" cy="60" rx="70" ry="50" fill="rgba(230,81,0,0.12)" stroke="#e65100" stroke-width="2"/>
  <text x="130" y="55" font-size="12" fill="#1565c0" font-weight="bold">A</text>
  <text x="180" y="55" font-size="12" fill="#e65100" font-weight="bold">B</text>
  <text x="90" y="80" font-size="10" fill="#555">P(A)</text>
  <text x="200" y="80" font-size="10" fill="#555">P(B)</text>
  <text x="155" y="65" font-size="11" fill="#c62828" font-weight="bold">AB</text>
  <text x="155" y="80" font-size="9" fill="#c62828">P(AB)</text>
  <text x="155" y="98" font-size="9" fill="#555">P(A∪B)=P(A)+P(B)-P(AB)</text>
  <rect x="300" y="15" rx="5" ry="5" width="90" height="100" fill="#faf8f5" stroke="#ddd" stroke-width="1"/>
  <text x="345" y="35" text-anchor="middle" font-size="10" font-weight="bold" fill="#555">样本空间S</text>
  <text x="345" y="55" text-anchor="middle" font-size="9" fill="#555">P(S)=1</text>
  <text x="345" y="70" text-anchor="middle" font-size="9" fill="#555">P(∅)=0</text>
  <text x="345" y="90" text-anchor="middle" font-size="9" fill="#2e7d32">0 ≤ P(A) ≤ 1</text>
</svg>

**排列与组合的区分**：排列考虑顺序（如"排队"问题），组合不考虑顺序（如"选人"问题）。使用时务必根据问题背景判断。

## 二、条件概率与公式体系

### 2.1 条件概率

条件概率描述的是"在事件B已经发生的条件下，事件A发生的概率"：

P(A|B) = P(AB) / P(B)

条件概率的核心思想是缩小样本空间——已知B发生后，可能的样本点缩减为B包含的那些。

### 2.2 乘法公式

乘法公式是条件概率的直接推论：

P(AB) = P(A) × P(B|A) = P(B) × P(A|B)

乘法公式用于计算多个事件同时发生的概率。当事件数量较多时，可以逐步展开：P(A₁A₂A₃) = P(A₁)P(A₂|A₁)P(A₃|A₁A₂)

### 2.3 全概率公式

全概率公式用于"由因推果"场景。如果事件A的发生受到多个互不相容的原因B₁,...,Bn的影响，且这些原因构成了样本空间的一个划分，那么：

P(A) = ΣP(Bi)P(A|Bi)

**典型应用场景**：一批产品由多个工厂生产，每个工厂的次品率不同，求从这批产品中随机抽取一个产品是次品的概率。

### 2.4 贝叶斯公式

贝叶斯公式是全概率公式的逆向应用——"由果推因"。已知结果A发生了，反推是由Bi引起的概率：

P(Bi|A) = P(Bi)P(A|Bi) / ΣP(Bj)P(A|Bj)

贝叶斯公式在实际中有着广泛的应用。例如垃圾邮件过滤——根据邮件内容推断它是垃圾邮件的概率。

## 三、典型例题精讲

**例1**（2024真题）：将标号为1,2,3,4的四个球随机排成一行，求第1号球在最右边或最左边的概率。

> 总排列数：4! = 24
> 1号球在最左边：3! = 6种（剩余3个球任意排列）
> 1号球在最右边：3! = 6种
> P = (6+6)/24 = 1/2

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 140" width="100%" height="140">
  <rect x="10" y="10" width="120" height="120" fill="rgba(25,118,210,0.08)" stroke="#1976d2" stroke-width="1.5"/>
  <text x="70" y="80" text-anchor="middle" font-size="10" fill="#1565c0">两人到达时间</text>
  <text x="70" y="95" text-anchor="middle" font-size="10" fill="#1565c0">坐标点 (x,y)</text>
  <text x="70" y="115" text-anchor="middle" font-size="9" fill="#555">0≤x≤60, 0≤y≤60</text>
  <line x1="10" y1="130" x2="130" y2="130" stroke="#555" stroke-width="1"/>
  <text x="70" y="140" text-anchor="middle" font-size="9" fill="#555">x (甲到达时间/min)</text>
  <text x="145" y="105" font-size="10" fill="#555">y</text>

  <rect x="180" y="10" width="120" height="120" fill="rgba(25,118,210,0.12)" stroke="#1976d2" stroke-width="1.5"/>
  <polygon points="180,25 265,10 300,10 300,85 215,130 180,130" fill="rgba(230,81,0,0.15)" stroke="#e65100" stroke-width="1.5" stroke-dasharray="4,2"/>
  <text x="240" y="50" text-anchor="middle" font-size="10" fill="#e65100">|x-y|≤15</text>
  <text x="240" y="65" text-anchor="middle" font-size="9" fill="#e65100">（能见面）</text>
  <text x="240" y="85" text-anchor="middle" font-size="9" fill="#555">总面积 = 60×60 = 3600</text>
  <text x="240" y="100" text-anchor="middle" font-size="9" fill="#555">不能见面 = 2×(½×45×45)</text>
  <text x="240" y="115" text-anchor="middle" font-size="9" fill="#555">= 2025</text>
  <text x="240" y="132" text-anchor="middle" font-size="10" font-weight="bold" fill="#1565c0">P = 1575/3600 = 7/16</text>
</svg>

**例2**（2024真题）：两人约定8点至9点会面，先到者等候15分钟，过时离去，求两人能见面的概率。

> 这是一个几何概型问题。设两人到达时间分别为x和y（以分钟为单位），x,y∈[0,60]。
> 能见面的条件是|x-y|≤15，即两人到达时间差不超过15分钟。
> 在60×60的坐标系上，能见面的区域是"带状"区域，面积=60×60 - 2×(1/2×45×45) = 3600-2025=1575
> P = 1575/3600 = 7/16

**例3**（2024真题 - 贝叶斯公式）：将两信息分别编码为A和B发送。A被误收作B的概率为0.02，B被误收作A的概率为0.01。信息A与B传送频繁程度为3:1。若收到的是A，求原发信息也是A的概率。

> 设事件：
> H₁ = "发出A"，H₂ = "发出B"
> E = "收到A"
>
> P(H₁) = 3/4, P(H₂) = 1/4
> P(E|H₁) = 1 - 0.02 = 0.98 （发出A且正确收到A）
> P(E|H₂) = 0.01（发出B被误收作A）
>
> 由贝叶斯公式：
> P(H₁|E) = P(H₁)P(E|H₁) / [P(H₁)P(E|H₁) + P(H₂)P(E|H₂)]
> = (0.75×0.98) / (0.75×0.98 + 0.25×0.01)
> = 0.735 / 0.7375 ≈ 0.9966
>
> 所以收到的信息是A时，原发信息也是A的概率约为99.66%。

**例4**（2017年数一考研题改编）：三个人独立地猜谜语，各人能猜出的概率分别为1/5, 1/3, 1/4。求至少有一人能猜出的概率。

> P(至少一人猜出) = 1 - P(三人均猜不出)
> P(三人均猜不出) = (4/5)×(2/3)×(3/4) = 24/60 = 2/5
> P(至少一人猜出) = 1 - 2/5 = 3/5
>
> 逻辑验证：三个人单独概率在0.2-0.33之间，至少一人猜出概率应该在0.488-0.6之间，3/5=0.6在合理范围内。
