from datetime import datetime
import json
import os
import pandas as pd
import streamlit as st

# Configuration de la page
st.set_page_config(
    page_title="SPM - Planificateur Endurance", page_icon="🏎️", layout="wide"
)

DRIVERS_FILE = "drivers.json"
CONFIG_FILE = "config_course.json"
DISPOS_FILE = "dispos.json"


def load_json(filename, default_val):
  if os.path.exists(filename):
    with open(filename, "r", encoding="utf-8") as f:
      try:
        return json.load(f)
      except json.JSONDecodeError:
        return default_val
  return default_val


def save_json(filename, data):
  with open(filename, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)


# Chargement des données
drivers = load_json(DRIVERS_FILE, [])
config = load_json(
    CONFIG_FILE,
    {
        "nom_course": "Course d'Endurance",
        "jours": ["Vendredi", "Samedi", "Dimanche"],
        "creneaux": ["2h00", "7h00", "12h00", "17h00", "22h00"],
    },
)
dispos = load_json(DISPOS_FILE, [])

# --- INTERFACE PRINCIPALE ---
st.title(f"🏎️ {config.get('nom_course', 'Planning Endurance')}")
st.markdown(
    "Sélectionne ton nom, choisis ton jour, ton créneau et indique ton statut"
    " pour la course."
)

if not drivers:
  st.warning(
      "⚠️ Aucun pilote trouvé dans `drivers.json`. Crée ton fichier de pilotes"
      " d'abord."
  )
else:
  # On sépare l'écran en deux : Inscription (Gauche) / Vue d'ensemble (Droite)
  col_form, col_view = st.columns([1, 2])

  with col_form:
    st.subheader("📝 Enregistrer mes dispos")

    with st.form("form_dispo"):
      selected_driver = st.selectbox("Pilote", drivers)

      # Les jours et créneaux proviennent directement de ta configuration !
      selected_jour = st.selectbox("Jour", config["jours"])
      selected_creneau = st.selectbox("Tranche horaire", config["creneaux"])

      statut = st.selectbox(
          "Statut",
          [
              "Disponible",
              "Fortement recommandé / Titulaire",
              "Absent / Indisponible",
          ],
      )
      commentaire = st.text_input("Commentaire (optionnel)")

      submitted = st.form_submit_button("Valider mon créneau")

      if submitted:
        # Nettoyage des doublons pour un même pilote sur le même créneau
        dispos = [
            d
            for d in dispos
            if not (
                d["driver"] == selected_driver
                and d["jour"] == selected_jour
                and d["creneau"] == selected_creneau
            )
        ]

        if "Absent" not in statut:
          new_entry = {
              "driver": selected_driver,
              "jour": selected_jour,
              "creneau": selected_creneau,
              "statut": statut,
              "commentaire": commentaire,
              "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
          }
          dispos.append(new_entry)

        save_json(DISPOS_FILE, dispos)
        st.success(f"Disponibilité enregistrée pour {selected_driver} !")
        st.rerun()

    # --- ESPACE ADMINISTRATEUR (C'est toi qui gères la course ici) ---
    with st.expander("⚙️ Configuration de la course (Admin)"):
      st.markdown(
          "Modifie les paramètres de la course. Cela mettra à jour les menus"
          " pour tout le monde."
      )

      with st.form("form_config"):
        new_nom_course = st.text_input(
            "Nom de la course", value=config.get("nom_course", "")
        )

        # Gestion des jours (sous forme de texte séparé par des virgules)
        jours_str = st.text_input(
            "Jours (séparés par une virgule)", value=", ".join(config["jours"])
        )

        # Gestion des créneaux (séparés par une virgule)
        creneaux_str = st.text_input(
            "Tranches horaires (séparées par une virgule)",
            value=", ".join(config["creneaux"]),
        )

        save_config_btn = st.form_submit_button("Mettre à jour la course")

        if save_config_btn:
          config["nom_course"] = new_nom_course
          config["jours"] = [j.strip() for j in jours_str.split(",")]
          config["creneaux"] = [c.strip() for c in creneaux_str.split(",")]

          save_json(CONFIG_FILE, config)
          st.success("Configuration de la course mise à jour avec succès !")
          st.rerun()

      if st.button("🗑️ Réinitialiser toutes les disponibilités"):
        save_json(DISPOS_FILE, [])
        st.success("Le planning a été remis à zéro.")
        st.rerun()

  with col_view:
    st.subheader("👀 Vue d'ensemble par Jour")

    if dispos:
      df = pd.DataFrame(dispos)

      # Sélecteur pour afficher un jour en particulier sous forme de grille/matrice
      jour_selectionne = st.selectbox(
          "Filtrer l'affichage par jour", config["jours"]
      )

      df_jour = df[df["jour"] == jour_selectionne]

      if not df_jour.empty:
        # Création du tableau croisé (Pilotes en lignes, Créneaux horaires en colonnes)
        pivot = (
            df_jour.pivot_table(
                index="driver",
                columns="creneau",
                values="statut",
                aggfunc="first",
            )
            .fillna("-")
        )
        st.dataframe(pivot, use_container_width=True)
      else:
        st.info(f"Aucune disponibilité enregistrée pour {jour_selectionne}.")

      st.markdown("---")
      st.subheader("📋 Liste brute complète")
      st.dataframe(
          df[
              ["driver", "jour", "creneau", "statut", "commentaire", "updated_at"]
          ].rename(
              columns={
                  "driver": "Pilote",
                  "jour": "Jour",
                  "creneau": "Créneau",
                  "statut": "Statut",
                  "commentaire": "Commentaire",
                  "updated_at": "Mis à jour le",
              }
          ),
          use_container_width=True,
          hide_index=True,
      )
    else:
      st.info(
          "Aucune disponibilité enregistrée pour le moment. Sois le premier à"
          " t'inscrire !"
      )