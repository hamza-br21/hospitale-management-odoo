# Gestion Hospitalière (Enhanced)

Ce module Odoo 17 permet de gérer les activités complètes d'un hôpital avec des fonctionnalités avancées.

## Fonctionnalités

### Gestion des Patients
- **Dossiers patients complets** : Nom, date de naissance, âge automatique, groupe sanguin, contact
- **Historique médical** : Suivi des rendez-vous, admissions, prescriptions et factures
- **Assurance santé** : Gestion des polices d'assurance avec calcul automatique de couverture
- **Smart buttons** : Accès rapide aux rendez-vous et factures depuis le dossier patient

### Gestion Médicale
- **Médecins** : Profils complets avec spécialisation, département et photo
- **Rendez-vous** : 
  - Types d'appointments (consultation, suivi, urgence, check-up)
  - Vue Kanban par état
  - Vue Calendrier pour planning
  - Durée configurable
- **Prescriptions** : 
  - Catalogue de médicaments intégré
  - Lignes de prescription avec dosage, fréquence et durée
  - Sélection automatique depuis le catalogue

### Infrastructure Hospitalière
- **Salles/Chambres** : 
  - Types multiples (générale, privée, USI, urgence, bloc opératoire)
  - Tarifs journaliers
  - Vue Kanban avec disponibilité en temps réel
- **Lits** : 
  - État (libre/occupé/maintenance)
  - Liaison automatique avec les admissions
  - Suivi du patient actuel
- **Départements** : Organisation par spécialités

### Admissions & Hospitalisation
- **Workflow complet** : Draft → Active → Discharged
- **Types d'admission** : Urgence, planifiée, observation
- **Médecin assigné** et diagnostic
- **Résumé de sortie**
- **Gestion automatique des lits**

### Facturation Avancée
- **Factures détaillées** avec lignes multiples
- **Types de charges** : Consultation, chambre, médicaments, procédures, tests
- **Intégration assurance** : 
  - Calcul automatique de la couverture
  - Montant patient à payer
- **Méthodes de paiement** : Espèces, carte, assurance, virement
- **Dates d'échéance**

### Catalogue Médicaments
- **Base complète** : Nom commercial, générique, force
- **Catégories** : Antibiotiques, antidouleurs, vitamines, etc.
- **Formes galéniques** : Comprimés, capsules, sirop, injection, crème
- **Gestion stock** avec prix unitaires
- **Dates de péremption**

## Installation et Exécution

### Pré-requis
- Odoo 17
- PostgreSQL

### Structure des dossiers
Assurez-vous que le dossier `gestion_hospitaliere` est dans votre chemin `addons_path` d'Odoo.

### Commandes Utiles

**1. Démarrer Odoo avec le module et les données de démo :**
```bash
./odoo-bin -d hospital_db -i gestion_hospitaliere --dev=all
```
*Note : Si vous utilisez Docker, assurez-vous de monter le volume et d'installer le module via l'interface ou la ligne de commande.*

**2. Mettre à jour le module (après modification du code) :**
```bash
./odoo-bin -d hospital_db -u gestion_hospitaliere
```

**3. Lancer les tests unitaires :**
```bash
./odoo-bin -d hospital_db -i gestion_hospitaliere --test-enable --stop-after-init
```

## Utilisation

### Configuration Initiale
1. **Départements** : Configuration → Departments
2. **Médicaments** : Medicines → Ajouter au catalogue
3. **Salles & Lits** : Rooms → Créer salles et lits
4. **Médecins** : Doctors → Ajouter médecins avec leurs spécialités

### Workflow Patient
1. **Enregistrer un patient** : Patients → Nouveau
   - Remplir informations personnelles et médicales
   - Ajouter assurance si applicable
2. **Créer un rendez-vous** : Appointments → Nouveau
   - Choisir patient, médecin, type et date
   - Vue calendrier disponible pour planning
3. **Hospitaliser** : Admissions → Nouveau
   - Sélectionner patient, médecin, type d'admission
   - Choisir lit disponible → Confirmer "Admit"
   - Le lit passe automatiquement en "Occupé"
4. **Prescrire** : Prescriptions → Nouveau
   - Ajouter lignes avec médicaments du catalogue
   - Dosage, fréquence, durée
5. **Facturer** : Billing → Nouveau
   - Lier à admission/rendez-vous
   - Ajouter lignes de facturation
   - Sélectionner assurance → Calcul automatique
   - Marquer comme "Paid"
6. **Sortie** : Admission → "Discharge"
   - Ajouter résumé de sortie
   - Le lit redevient "Free"

## Données de Démonstration
Le module inclut des données complètes :
- **Patients** : John Doe, Jane Smith, Baby Doe (avec assurance)
- **Médecins** : Dr. House (Neurologie), Dr. Cameron (Cardiologie), Dr. Wilson (Pédiatrie)
- **Départements** : Cardiologie, Neurologie, Pédiatrie
- **Médicaments** : Paracetamol, Amoxicillin (avec prix et stock)
- **Salles & Lits** : 2 salles, 3 lits configurés
- **Admissions & Factures** : Exemples complets avec lignes détaillées

## Vues Disponibles
- **Tree** : Listes standards
- **Form** : Formulaires détaillés avec smart buttons
- **Kanban** : Rendez-vous (par état), Salles (avec disponibilité)
- **Calendar** : Planning des rendez-vous
- **Dashboard** : Vue d'ensemble (menu principal)
