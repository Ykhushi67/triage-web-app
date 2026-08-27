"""
PatientTriage.ai - Text Feature Extraction for Clinical Symptoms & Notes.

Uses domain-aware sublinear TF-IDF with character + word n-grams to handle
medical abbreviations, typos (sob, n/v, chst), and clinical shorthand.
"""

import os
import pickle
import numpy as np
import pandas as pd
from typing import List, Tuple, Any
from sklearn.feature_extraction.text import TfidfVectorizer


class ClinicalTextExtractor:
    """
    Domain-aware TF-IDF extractor with character-level n-grams to
    handle medical typos (e.g. 'chst', 'throut', 'hedache').
    """

    def __init__(self, max_features: int = 64, ngram_range: Tuple[int, int] = (1, 2)):
        self.max_features = max_features
        self.ngram_range = ngram_range
        # Word-level vectorizer for clinical concepts
        self.word_vectorizer = TfidfVectorizer(
            max_features=max_features,
            ngram_range=ngram_range,
            sublinear_tf=True,
            stop_words="english",
            lowercase=True,
            min_df=2,
        )
        # Char-level vectorizer to handle typos and abbreviations
        self.char_vectorizer = TfidfVectorizer(
            max_features=32,
            analyzer="char_wb",
            ngram_range=(3, 4),
            sublinear_tf=True,
            lowercase=True,
            min_df=2,
        )
        self.is_fitted = False

    def fit_transform(self, texts: pd.Series) -> np.ndarray:
        """Fits both vectorizers and returns combined feature matrix."""
        clean = texts.fillna("").astype(str)
        word_feat = self.word_vectorizer.fit_transform(clean).toarray()
        char_feat = self.char_vectorizer.fit_transform(clean).toarray()
        self.is_fitted = True
        return np.hstack([word_feat, char_feat]).astype(np.float32)

    def transform(self, texts: Any) -> np.ndarray:
        """Transforms new text into features."""
        if not self.is_fitted:
            raise ValueError("ClinicalTextExtractor is not fitted yet.")
        if isinstance(texts, str):
            clean = [texts]
        elif isinstance(texts, (pd.Series, list)):
            clean = [str(t) if pd.notna(t) else "" for t in texts]
        else:
            clean = [str(texts)]
        word_feat = self.word_vectorizer.transform(clean).toarray()
        char_feat = self.char_vectorizer.transform(clean).toarray()
        return np.hstack([word_feat, char_feat]).astype(np.float32)

    def get_feature_names(self) -> List[str]:
        if not self.is_fitted:
            return []
        word_names = [f"word_{n}" for n in self.word_vectorizer.get_feature_names_out()]
        char_names = [f"char_{n}" for n in self.char_vectorizer.get_feature_names_out()]
        return word_names + char_names

    def n_features(self) -> int:
        return self.max_features + 32

    def save(self, filepath: str):
        with open(filepath, "wb") as f:
            pickle.dump(self, f)

    @classmethod
    def load(cls, filepath: str) -> "ClinicalTextExtractor":
        with open(filepath, "rb") as f:
            return pickle.load(f)
