"""
Generates the Google Colab Notebook: ml/AI_Career_Prediction_Model_Training.ipynb
Fully formatted Jupyter notebook with Markdown explanations, code cells, visual plots,
multi-model benchmarks, and an interactive inference widget.
"""

import json
from pathlib import Path


def create_colab_notebook():
    notebook = {
        "nbformat": 4,
        "nbformat_minor": 0,
        "metadata": {
            "colab": {
                "name": "AI_Career_Prediction_Model_Training.ipynb",
                "provenance": [],
                "toc_visible": True,
            },
            "kernelspec": {
                "name": "python3",
                "display_name": "Python 3"
            },
            "language_info": {
                "name": "python"
            }
        },
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "# Strathmore University - Faculty of Information Technology\n",
                    "## BSc in Informatics and Computer Science - Final Year Capstone Project\n",
                    "### **Project Title:** Intelligent Career Guidance Assistant Using Retrieval-Augmented Generation (RAG)\n",
                    "**Student Name:** Kimathi John Mwiti (Student ID: 169900)  \n",
                    "**Supervisor:** Madam Julliet Kirui  \n",
                    "**Component:** Stage 1 Machine Learning Career Classification Model  \n",
                    "\n",
                    "---\n",
                    "\n",
                    "### **Notebook Objective:**\n",
                    "This notebook implements and rigorously benchmarks the **Stage 1 Machine Learning Classifier** for predicting a student's optimal Computer Science & Informatics career pathway based on their **skills**, **qualifications**, and **experience**.\n",
                    "\n",
                    "#### **Research Methodology:**\n",
                    "1. **Dataset**: Balanced subset of Kaggle Job Descriptions (32,500 records across 13 core tech categories, exactly 2,500 per class).\n",
                    "2. **Feature Extraction**: Sublinear TF-IDF vectorization with n-gram extraction (unigrams + bigrams).\n",
                    "3. **Regularization & Generalization**: Controlled hyperparameter tuning to eliminate both **underfitting** and **overfitting**.\n",
                    "4. **Multi-Model Benchmark**: Comparison of Logistic Regression, Calibrated LinearSVC, Multinomial Naive Bayes, and Depth-Limited Random Forest.\n",
                    "5. **Interactive Testing**: Real-time career prediction function returning top-3 recommended roles with confidence probabilities."
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "### Step 1: Install & Import Required Libraries"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# Install core dependencies if running in a fresh Google Colab environment\n",
                    "!pip install -q pandas numpy scikit-learn matplotlib seaborn joblib\n",
                    "\n",
                    "import os\n",
                    "import json\n",
                    "import numpy as np\n",
                    "import pandas as pd\n",
                    "import matplotlib.pyplot as plt\n",
                    "import seaborn as sns\n",
                    "import joblib\n",
                    "\n",
                    "from sklearn.model_selection import train_test_split\n",
                    "from sklearn.feature_extraction.text import TfidfVectorizer\n",
                    "from sklearn.linear_model import LogisticRegression\n",
                    "from sklearn.svm import LinearSVC\n",
                    "from sklearn.calibration import CalibratedClassifierCV\n",
                    "from sklearn.naive_bayes import MultinomialNB\n",
                    "from sklearn.ensemble import RandomForestClassifier\n",
                    "from sklearn.pipeline import Pipeline\n",
                    "from sklearn.metrics import (\n",
                    "    accuracy_score,\n",
                    "    precision_recall_fscore_support,\n",
                    "    classification_report,\n",
                    "    confusion_matrix,\n",
                    "    ConfusionMatrixDisplay,\n",
                    ")\n",
                    "\n",
                    "print(\"Libraries successfully imported!\")"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "### Step 2: Load the Curated Tech Career Dataset\n",
                    "You can upload `tech_career_dataset.csv` directly to Colab's file panel or load it from Google Drive / workspace."
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# If running in Colab, upload tech_career_dataset.csv or adjust path\n",
                    "dataset_path = 'tech_career_dataset.csv'\n",
                    "\n",
                    "if not os.path.exists(dataset_path):\n",
                    "    # Check fallback path in repo\n",
                    "    if os.path.exists('ml/data/tech_career_dataset.csv'):\n",
                    "        dataset_path = 'ml/data/tech_career_dataset.csv'\n",
                    "    else:\n",
                    "        print(\"Please upload tech_career_dataset.csv into the current working directory.\")\n",
                    "\n",
                    "df = pd.read_csv(dataset_path)\n",
                    "print(f\"Dataset shape: {df.shape[0]:,} rows, {df.shape[1]} columns\")\n",
                    "print(\"\\nFirst 3 rows:\")\n",
                    "display(df[['target_category', 'skills', 'qualifications', 'experience']].head(3))\n",
                    "\n",
                    "# Verify balanced class distribution\n",
                    "plt.figure(figsize=(10, 4))\n",
                    "df['target_category'].value_counts().plot(kind='bar', color='#3b82f6', edgecolor='black')\n",
                    "plt.title('Balanced Distribution of Tech Career Roles (N=32,500)', fontsize=12, fontweight='bold')\n",
                    "plt.xlabel('Target Career Role')\n",
                    "plt.ylabel('Number of Samples')\n",
                    "plt.xticks(rotation=45, ha='right')\n",
                    "plt.grid(axis='y', linestyle='--', alpha=0.5)\n",
                    "plt.show()"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "### Step 3: Feature Engineering & Train/Test Split (Anti-Overfitting Setup)\n",
                    "To ensure our model generalizes reliably and neither **underfits** nor **overfits**:\n",
                    "1. We engineer a structured composite feature: `\"Qualifications: {quals}. Experience: {exp}. Skills: {skills}.\"`\n",
                    "2. We use a **Stratified 80/20 train/test split** so all 13 categories maintain equal representation.\n",
                    "3. We use **TF-IDF with sublinear term scaling** (`sublinear_tf=True`), `min_df=3` (to discard idiosyncratic typos), `max_df=0.85` (to filter ubiquitous stopwords), and an n-gram range of `(1, 2)` (to capture both single skills and phrases like *'cloud security'* or *'deep learning'*)."
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "X = df['feature_text'].fillna('')\n",
                    "y = df['target_category']\n",
                    "\n",
                    "# Stratified train/test split (80% train, 20% test)\n",
                    "X_train, X_test, y_train, y_test = train_test_split(\n",
                    "    X, y, test_size=0.20, random_state=42, stratify=y\n",
                    ")\n",
                    "\n",
                    "print(f\"Training samples: {len(X_train):,}\")\n",
                    "print(f\"Testing samples:  {len(X_test):,}\")\n",
                    "\n",
                    "tfidf_params = {\n",
                    "    'sublinear_tf': True,\n",
                    "    'min_df': 3,\n",
                    "    'max_df': 0.85,\n",
                    "    'ngram_range': (1, 2),\n",
                    "    'max_features': 8000\n",
                    "}"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "### Step 4: Model Training & Rigorous Multi-Model Benchmarking\n",
                    "We train and benchmark 4 distinct classification algorithms:\n",
                    "1. **Logistic Regression (L2)**: Multinomial linear classifier with balanced weight decay.\n",
                    "2. **Calibrated LinearSVC**: Margin-maximizing support vector classifier with Platt scaling for well-calibrated probabilities.\n",
                    "3. **Multinomial Naive Bayes**: Probabilistic baseline with Laplace smoothing.\n",
                    "4. **Random Forest (Depth-limited)**: Ensemble bagging model with depth constraints (`max_depth=25`) to prevent overfitting."
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "models = {\n",
                    "    'Logistic Regression (L2)': LogisticRegression(\n",
                    "        C=1.0, max_iter=1000, solver='lbfgs', random_state=42\n",
                    "    ),\n",
                    "    'Calibrated LinearSVC': CalibratedClassifierCV(\n",
                    "        estimator=LinearSVC(C=0.5, dual='auto', max_iter=2000, random_state=42),\n",
                    "        method='sigmoid',\n",
                    "        cv=3\n",
                    "    ),\n",
                    "    'Multinomial Naive Bayes': MultinomialNB(alpha=0.5),\n",
                    "    'Random Forest (Depth-limited)': RandomForestClassifier(\n",
                    "        n_estimators=120, max_depth=25, min_samples_split=5, min_samples_leaf=2, random_state=42, n_jobs=-1\n",
                    "    )\n",
                    "}\n",
                    "\n",
                    "results = {}\n",
                    "fitted_pipelines = {}\n",
                    "\n",
                    "print(\"=\" * 75)\n",
                    "print(f\"{'Model Architecture':<32} | {'Train Acc':<10} | {'Test Acc':<9} | {'Test F1':<8} | {'Gap (Train-Test)'}\")\n",
                    "print(\"-\" * 75)\n",
                    "\n",
                    "for name, clf in models.items():\n",
                    "    pipe = Pipeline([\n",
                    "        ('tfidf', TfidfVectorizer(**tfidf_params)),\n",
                    "        ('clf', clf)\n",
                    "    ])\n",
                    "    \n",
                    "    pipe.fit(X_train, y_train)\n",
                    "    fitted_pipelines[name] = pipe\n",
                    "    \n",
                    "    train_preds = pipe.predict(X_train)\n",
                    "    test_preds = pipe.predict(X_test)\n",
                    "    \n",
                    "    train_acc = accuracy_score(y_train, train_preds)\n",
                    "    test_acc = accuracy_score(y_test, test_preds)\n",
                    "    gap = train_acc - test_acc\n",
                    "    \n",
                    "    prec, rec, f1, _ = precision_recall_fscore_support(y_test, test_preds, average='weighted', zero_division=0)\n",
                    "    macro_prec, macro_rec, macro_f1, _ = precision_recall_fscore_support(y_test, test_preds, average='macro', zero_division=0)\n",
                    "    \n",
                    "    results[name] = {\n",
                    "        'train_acc': train_acc,\n",
                    "        'test_acc': test_acc,\n",
                    "        'test_f1': f1,\n",
                    "        'macro_f1': macro_f1,\n",
                    "        'weighted_prec': prec,\n",
                    "        'weighted_rec': rec,\n",
                    "        'gap': gap\n",
                    "    }\n",
                    "    \n",
                    "    print(f\"{name:<32} | {train_acc*100:6.2f}%   | {test_acc*100:6.2f}%  | {f1*100:6.2f}%  | {gap*100:4.2f}%\")\n",
                    "\n",
                    "print(\"=\" * 75)\n",
                    "\n",
                    "best_model_name = max(results.keys(), key=lambda k: results[k]['test_f1'])\n",
                    "best_pipe = fitted_pipelines[best_model_name]\n",
                    "print(f\"\\n>>> WINNING MODEL: {best_model_name} (Test F1: {results[best_model_name]['test_f1']*100:.2f}%) <<<\")"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "### Step 5: Visualizing Comparative Performance & Generalization\n",
                    "We plot Train vs. Test Accuracy and F1-score across all 4 models to empirically prove the absence of overfitting (minimal gap between Train and Test)."
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# Model comparison bar chart\n",
                    "model_names = list(results.keys())\n",
                    "train_scores = [results[m]['train_acc'] * 100 for m in model_names]\n",
                    "test_scores = [results[m]['test_acc'] * 100 for m in model_names]\n",
                    "f1_scores = [results[m]['test_f1'] * 100 for m in model_names]\n",
                    "\n",
                    "x = np.arange(len(model_names))\n",
                    "width = 0.25\n",
                    "\n",
                    "fig, ax = plt.subplots(figsize=(12, 6))\n",
                    "ax.bar(x - width, train_scores, width, label='Train Accuracy', color='#3b82f6', alpha=0.85)\n",
                    "ax.bar(x, test_scores, width, label='Test Accuracy', color='#10b981', alpha=0.85)\n",
                    "ax.bar(x + width, f1_scores, width, label='Test F1-Score', color='#8b5cf6', alpha=0.85)\n",
                    "\n",
                    "ax.set_ylabel('Performance (%)', fontsize=12)\n",
                    "ax.set_title('Multi-Model Comparison: Training vs Generalization Test Scores', fontsize=14, fontweight='bold')\n",
                    "ax.set_xticks(x)\n",
                    "ax.set_xticklabels([m.replace(' ', '\\n') for m in model_names], fontsize=10)\n",
                    "ax.set_ylim(0, 105)\n",
                    "ax.legend(loc='lower right', frameon=True)\n",
                    "ax.grid(axis='y', linestyle='--', alpha=0.4)\n",
                    "plt.tight_layout()\n",
                    "plt.show()"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "### Step 6: Detailed Classification Report & Confusion Matrix\n",
                    "Let's inspect per-class Precision, Recall, and F1-Scores along with the normalized confusion matrix for the winning model."
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "y_pred_best = best_pipe.predict(X_test)\n",
                    "print(f\"Classification Report for {best_model_name}:\\n\")\n",
                    "print(classification_report(y_test, y_pred_best, zero_division=0))\n",
                    "\n",
                    "# Plot normalized confusion matrix\n",
                    "fig, ax = plt.subplots(figsize=(12, 10))\n",
                    "short_labels = [c.replace(' / ', '/').replace('Engineer', 'Eng').replace('Developer', 'Dev') for c in best_pipe.classes_]\n",
                    "ConfusionMatrixDisplay.from_predictions(\n",
                    "    y_test,\n",
                    "    y_pred_best,\n",
                    "    labels=best_pipe.classes_,\n",
                    "    display_labels=short_labels,\n",
                    "    normalize='true',\n",
                    "    cmap='Blues',\n",
                    "    values_format='.2f',\n",
                    "    xticks_rotation=45,\n",
                    "    ax=ax,\n",
                    "    colorbar=True\n",
                    ")\n",
                    "plt.title(f'Normalized Confusion Matrix ({best_model_name})', fontsize=13, fontweight='bold', pad=12)\n",
                    "plt.xlabel('Predicted Category', fontsize=11)\n",
                    "plt.ylabel('True Category', fontsize=11)\n",
                    "plt.tight_layout()\n",
                    "plt.show()"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "### Step 7: Interactive Real-Time Career Prediction Function\n",
                    "Test the trained pipeline on realistic Strathmore student profiles to see top-3 career recommendations and probability distributions."
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "def predict_student_career(skills, qualifications='BSc Computer Science', experience='0 to 1 Years'):\n",
                    "    composite_input = f\"Qualifications: {qualifications}. Experience: {experience}. Skills: {skills}.\"\n",
                    "    probs = best_pipe.predict_proba([composite_input])[0]\n",
                    "    classes = best_pipe.classes_\n",
                    "    \n",
                    "    top_indices = np.argsort(-probs)[:3]\n",
                    "    \n",
                    "    print(f\"\\n--- Student Profile Evaluation ---\")\n",
                    "    print(f\"Qualifications: {qualifications}\")\n",
                    "    print(f\"Experience:     {experience}\")\n",
                    "    print(f\"Skills:         {skills}\")\n",
                    "    print(f\"\\nTop 3 Career Recommendations:\")\n",
                    "    for rank, idx in enumerate(top_indices, start=1):\n",
                    "        print(f\"  {rank}. {classes[idx]:<30} -> Confidence: {probs[idx]*100:.1f}%\")\n",
                    "    print(\"-\" * 45)\n",
                    "\n",
                    "# Test Case 1: Data Science / Machine Learning Student\n",
                    "predict_student_career(\n",
                    "    skills=\"Python, SQL, pandas, scikit-learn, PyTorch, statistics, data visualization, exploratory data analysis\",\n",
                    "    qualifications=\"BSc Informatics\",\n",
                    "    experience=\"Final Year Student\"\n",
                    ")\n",
                    "\n",
                    "# Test Case 2: Full-Stack / Backend Student\n",
                    "predict_student_career(\n",
                    "    skills=\"Java, Spring Boot, REST APIs, PostgreSQL, Docker, Git, microservices, Maven\",\n",
                    "    qualifications=\"BSc Computer Science\",\n",
                    "    experience=\"0 to 1 Years\"\n",
                    ")\n",
                    "\n",
                    "# Test Case 3: Cybersecurity Enthusiast\n",
                    "predict_student_career(\n",
                    "    skills=\"Network security, Wireshark, penetration testing, Kali Linux, firewall configuration, OWASP Top 10\",\n",
                    "    qualifications=\"BBIT\",\n",
                    "    experience=\"Internship\"\n",
                    ")"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "### Step 8: Save and Export the Trained Pipeline\n",
                    "We serialize the complete winning pipeline (`TfidfVectorizer` + `Classifier`) into `career_model.pkl` for deployment into our FastAPI backend."
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "model_filename = 'career_model.pkl'\n",
                    "joblib.dump(best_pipe, model_filename)\n",
                    "print(f\"Model pipeline successfully saved to {model_filename}!\")\n",
                    "print(f\"File size: {os.path.getsize(model_filename) / (1024 * 1024):.2f} MB\")"
                ]
            }
        ]
    }

    out_path = Path("ml/AI_Career_Prediction_Model_Training.ipynb")
    out_path.write_text(json.dumps(notebook, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Generated Colab notebook at: {out_path}")


if __name__ == "__main__":
    create_colab_notebook()
