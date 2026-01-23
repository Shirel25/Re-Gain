import numpy as np
from sklearn.cluster import KMeans
from collections import deque


class KMeansModel:
    def __init__(self, n_clusters=3, buffer_size=200):
        self.n_clusters = n_clusters
        self.buffer = deque(maxlen=buffer_size)

        self.model = None
        self.fitted = False

    def add_sample(self, features):
        """
        features: array-like (ex: [arm_activation])
        """
        self.buffer.append(features)

    def fit(self):
        if len(self.buffer) < self.n_clusters * 10:
            return False  # pas assez de données

        X = np.array(self.buffer)

        # garde fou : éviter erreur si pas assez de clusters uniques
        if len(np.unique(X)) < self.n_clusters:
            return False
        
        self.model = KMeans(n_clusters=self.n_clusters, n_init=10)
        self.model.fit(X)

        self.fitted = True
        return True

    def predict(self, features):
        if not self.fitted:
            return None

        features = np.array(features).reshape(1, -1)
        return self.model.predict(features)[0]

    def get_cluster_order(self):
        """
        Returns cluster indices sorted by centroid value.
        Lowest centroid first.
        """
        if not self.fitted:
            return None

        centroids = self.model.cluster_centers_.flatten()
        return list(np.argsort(centroids))
