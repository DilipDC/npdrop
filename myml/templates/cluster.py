# Description: K-means clustering with WCSS elbow plot and cluster visualization
from sklearn.cluster import KMeans

x=df[['Annual Income (k$)','Spending Score (1-100)']]
wcss=[]
for k in range(1,11):
  km=KMeans(n_clusters=k,random_state=42)
  km.fit(x)
  wcss.append(km.inertia_)


sns.lineplot(x=range(1,11),y=wcss,marker='o')


model=KMeans(n_clusters=5,random_state=42)
df['cluster']=model.fit_predict(x)
sns.scatterplot(data=df,x='Annual Income (k$)',y='Spending Score (1-100)',hue='cluster')