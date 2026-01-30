# Dashboard Sites PV - Streamlit + Supabase

Dashboard de gestion des sites photovoltaïques.

## Lancer dans GitHub Codespaces

### 1. Créer le repo GitHub
- Créer un nouveau repo sur GitHub
- Y pousser ces fichiers

### 2. Ouvrir dans Codespaces
- Depuis le repo GitHub, cliquer sur **Code** → **Codespaces** → **Create codespace**

### 3. Configurer les credentials
Dans le terminal Codespaces :
```bash
mkdir -p .streamlit
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Puis éditer `.streamlit/secrets.toml` avec tes vraies clés (déjà pré-remplies dans l'example).

### 4. Installer et lancer
```bash
pip install -r requirements.txt
streamlit run app.py
```

Codespaces va détecter le port 8501 et te proposer un lien pour ouvrir l'app.

## Déployer sur Streamlit Cloud (pour partager avec collègues)

1. Connecter ton repo GitHub à [share.streamlit.io](https://share.streamlit.io)
2. Dans les settings de l'app, ajouter les secrets :
   ```toml
   [supabase]
   url = "https://jdgirhqkikgruabnrbgf.supabase.co"
   key = "ta_clé_anon"
   ```
3. Déployer

## Structure
```
├── app.py                      # Application principale
├── requirements.txt            # Dépendances Python
├── .streamlit/
│   └── secrets.toml.example    # Template de configuration
└── README.md
```
