import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans

df = pd.read_csv("Mall_Customers.csv")
x=df[['Annual Income (k$)','Spending Score (1-100)']]


for k in range(1, 11):
    km = KMeans(n_clusters=k, random_state=42,)
    km.fit(X)
    wcss.append(km.inertia_)


sns.lineplot(x=range(1,11),y=wcss,marker='o')

model = KMeans(n_clusters=5, random_state=42)
df["cluster"] = model.fit_predict(X)
sns.scatterplot(data=df,x='Annual Income (k$)',y='Spending Score (1-100)',hue='cluster')
