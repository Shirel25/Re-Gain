# 🎮 Re:Gain — Jeu adaptatif contrôlé par signaux EMG

## 🖼️ Aperçu du prototype

![Gameplay](assets/game.png)
Le prototype prend la forme d’un jeu de type *runner 2D* :

- Le personnage avance horizontalement en fonction de l’activation musculaire du bras
- Les sauts sont déclenchés par l’activation de la jambe
- Des obstacles apparaissent dynamiquement
- Des barres de feedback visuel affichent l’effort du bras et de la jambe en temps réel

## 📌 Présentation du projet

**Re:Gain** est un jeu de type *runner 2D adaptatif* visant à explorer les **interactions homme–machine basées sur des signaux physiologiques**, en particulier l’EMG (électromyographie).

Le gameplay s’adapte dynamiquement à l’**effort musculaire du joueur**, mesuré à partir de signaux EMG réels ou simulés, grâce à un **pipeline d’interprétation basé sur l’intelligence artificielle**.

Le projet met l’accent sur :
- l’adaptation en temps réel (*boucle courte*),
- l’adaptation progressive de la difficulté (*boucle longue*),
- la robustesse face à des signaux physiologiques bruités ou indisponibles.

---

## 🎯 Objectifs

- Concevoir un jeu contrôlé par l’**activation musculaire** plutôt que par des entrées classiques
- Utiliser une **approche non supervisée (K-means)** pour interpréter les signaux EMG sans seuils fixes
- Adapter la difficulté du jeu à la **performance et à la fatigue** du joueur
- Proposer une **architecture logicielle modulaire et extensible**, applicable à des contextes de rééducation ludifiée

---

## 🧠 Architecture du système

L’architecture sépare clairement l’acquisition du signal, son interprétation par IA, et l’adaptation du gameplay.

```
Re-Gain/
│
├── main.py                  # Point d’entrée du jeu
│
├── input/
│   ├── fake_emg.py           # Génération de signaux EMG simulés
│   ├── emg.py                # Acquisition EMG réelle (BITalino)
│   ├── input_manager.py      # Interprétation des signaux & logique de contrôle
│   └── keyboard.py           # Mode clavier (fallback / debug)
│
├── models/
│   └── k_means_model.py      # Modèles de clustering K-means
│
├── game/
│   ├── game.py               # Boucle de jeu & adaptation de la difficulté
│   └── feedback_bars.py      # Biofeedback visuel (bras / jambe)
│
├── entities/
│   ├── player.py             # Physique et mouvements du joueur
│   ├── obstacle.py           # Gestion des obstacles
│   └── flag.py               # Marqueur de fin de parcours
│
├── calibration/
│ └── * # Scripts de calibration EMG (baseline, max activation)
|
├── ReGain_emg_test/
│ └── * # Scripts de test et de validation des signaux EMG
|
├── assets/                   # Ressources graphiques
└── Docs/                     # Documentation du projet
```

---

## 🔁 Boucles de contrôle

### 🔹 Boucle courte — Adaptation temps réel
- Exécutée **à chaque frame**
- Interprète l’activation EMG pour :
  - déclencher le déplacement
  - moduler la vitesse
  - autoriser le saut
- Objectif : interaction fluide, faible latence

### 🔹 Boucle longue — Adaptation progressive
- Exécutée sur une **fenêtre temporelle plus large**
- Agrège des métriques de performance :
  - vitesse moyenne (indicateur d’effort)
  - stabilité du contrôle
  - qualité des sauts
- Adapte dynamiquement l’environnement de jeu :
  - la fréquence des obstacles
  - leur densité
  - la complexité globale du parcours

---

## 🤖 Interprétation EMG & Intelligence Artificielle

### Pipeline de traitement

1. Acquisition du signal EMG (simulée dans la version actuelle du prototype)
2. Extraction d’une **valeur d’activation musculaire** par fenêtre temporelle
3. **Clustering non supervisé (K-means)**
4. Interprétation fonctionnelle des clusters pour le gameplay

### Modèles K-means

Deux modèles indépendants sont utilisés :

- **Bras** (`n_clusters = 3`)
  - REST (repos)
  - ACTIVE (contraction modérée)
  - OVERLOAD (effort élevé)

- **Jambe** (`n_clusters = 2`)
  - REST
  - ACTIVE

Les modèles K-means sont **ré-entraînés périodiquement** sur une fenêtre glissante d’activations récentes afin de :
- éviter des seuils fixes arbitraires,
- s’adapter au comportement de l’utilisateur,
- conserver une classification stable pendant le jeu.

> Le système apprend des **seuils d’activation relatifs**, spécifiques à l’interaction, et non une vérité physiologique médicale.

---

## 🧪 Modélisation de la fatigue

La fatigue est estimée à partir d’**indicateurs comportementaux**, tels que :
- la durée d’activation continue,
- la persistance de l’effort sans phase de récupération.

Lorsqu’un état de fatigue est détecté :
- une pause est suggérée au joueur via un message dédié,
- la progression du jeu est temporairement interrompue jusqu’à reprise volontaire.

Ce modèle est **exploratoire** et destiné à l’adaptation de l’interaction, non à un diagnostic clinique.

---

## 🕹️ Modes d’interaction

- **Clavier** : mode de référence / debug
- **EMG simulé** (*Fake EMG*) : mode principal
- **Double EMG réel** (*Dual EMG*) : expérimental (BITalino)

---

## 🚀 Lancer le projet

### Prérequis
- Python ≥ 3.9
- `pygame`
- `numpy`
- `scikit-learn`

### Exécution
```bash
python main.py
```

Par défaut, le jeu démarre en mode EMG simulé.

### ⚠️ Limites actuelles
- L’acquisition EMG réelle dépend du matériel (BITalino) et reste difficile à stabiliser
- Le modèle de fatigue est est volontairement simplifié et repose sur des indicateurs comportementaux
- Aucune validation clinique n’est revendiquée

### 🔮 Perspectives
- Réintégration robuste de capteurs EMG réels
- Adaptation plus fine du gameplay
- Études utilisateurs en contexte de rééducation

### 👥 Auteurs
Projet réalisé dans le cadre d’un Master en Intelligence Artificielle,
axé sur l’interaction adaptative et les interfaces physiologiques.