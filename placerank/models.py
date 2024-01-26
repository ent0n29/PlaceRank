"""
This module contains the definition of a `IRModel`, aka a search engine stack:
    - preprocessing
        - lexer
        - [parser]
        - stopwords filtering
        - [stemming | lemmatization]
        - [Q-gram generation]
    - [query expansion | lexical substitution | soundex]
    - [tolerant] retrieval
        - model. Eg.:
            - BIM
            - BM25
            - vector space model
            - W2V
        - weighting strategy. Eg.:
            - binary
            - TF-IDF
    - [ranking]
"""
from __future__ import annotations
from dataclasses import dataclass
from operator import index
from placerank.views import ResultView, QueryView
from abc import ABC, abstractmethod
from whoosh.analysis.analyzers import CompositeAnalyzer
from whoosh.scoring import WeightingModel
from whoosh.searching import Results
from whoosh.index import Index
from typing import List


class IRModel(ABC):
    def __init__(
        self,
        index: Index,
        preprocessing_pipeline: CompositeAnalyzer,
        tolerant_retrieval_service: TolerantRetrievalService,
        retrieval_model: RetrievalModel
    ):
        self._index = index
        self._preprocessing_pipeline = preprocessing_pipeline
        self._tolerant_retrieval_service = tolerant_retrieval_service
        self._retrieval_model = retrieval_model

    
    @abstractmethod
    def search(self, query: QueryView) -> List[ResultView]:
        ...


class TolerantRetrievalService(ABC):
    """
    
    """
    @abstractmethod
    def expand(query: str) -> str:
        ...


class TolerantRetrievalMock(TolerantRetrievalService):
    """
    A mock object that does nothing on the query
    """
    def expand(query: str) -> str:
        return query


class RetrievalModel(ABC):
    def __init__(self, index: Index, weighting_model: WeightingModel):
        self._index = index
        self._weighting_model = weighting_model

    @abstractmethod
    def search(self, query: str) -> Results:
        ...