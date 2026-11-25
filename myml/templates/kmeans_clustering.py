# Description: Scale features and run K-means clustering
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
X_scaled = StandardScaler().fit_transform(X)
model = KMeans(n_clusters=3, random_state=42, n_init="auto")
labels = model.fit_predict(X_scaled)
print("Cluster labels:", labels)
