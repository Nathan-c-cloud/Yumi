# user_profile.py - Gestion des profils utilisateurs pour personnaliser les scores YUmi

from enum import Enum
from dataclasses import dataclass
from typing import List, Optional

class AgeGroup(Enum):
    CHILD = "child"          # 3-12 ans
    TEENAGER = "teenager"    # 13-17 ans
    ADULT = "adult"          # 18-64 ans
    SENIOR = "senior"        # 65+ ans

class ActivityLevel(Enum):
    SEDENTARY = "sedentary"      # Peu d'activité
    LIGHT = "light"              # Activité légère
    MODERATE = "moderate"        # Activité modérée
    ACTIVE = "active"            # Très actif
    VERY_ACTIVE = "very_active"  # Extrêmement actif

class DietaryRestriction(Enum):
    NONE = "none"
    VEGETARIAN = "vegetarian"
    VEGAN = "vegan"
    GLUTEN_FREE = "gluten_free"
    LACTOSE_FREE = "lactose_free"
    HALAL = "halal"
    KOSHER = "kosher"
    LOW_SODIUM = "low_sodium"
    DIABETIC = "diabetic"

class HealthGoal(Enum):
    MAINTAIN_WEIGHT = "maintain_weight"
    LOSE_WEIGHT = "lose_weight"
    GAIN_WEIGHT = "gain_weight"
    BUILD_MUSCLE = "build_muscle"
    IMPROVE_HEALTH = "improve_health"
    REDUCE_SUGAR = "reduce_sugar"
    INCREASE_PROTEIN = "increase_protein"

@dataclass
class UserProfile:
    """Profil utilisateur pour personnaliser les scores YUmi"""

    # Informations de base
    name: str
    age_group: AgeGroup
    activity_level: ActivityLevel

    # Restrictions alimentaires et allergies
    dietary_restrictions: List[DietaryRestriction]
    allergies: List[str]  # Liste d'allergènes (ex: "nuts", "eggs", "milk")

    # Objectifs de santé
    health_goals: List[HealthGoal]

    # Préférences personnelles
    alcohol_allowed: bool = False
    max_sugar_tolerance: Optional[float] = None  # g/100g
    max_sodium_tolerance: Optional[float] = None  # g/100g
    min_fiber_preference: Optional[float] = None  # g/100g
    min_protein_preference: Optional[float] = None  # g/100g

    # Facteurs de pondération personnalisés (-1.0 à 1.0)
    sugar_sensitivity: float = 0.0      # Plus élevé = plus restrictif sur le sucre
    sodium_sensitivity: float = 0.0     # Plus élevé = plus restrictif sur le sodium
    calorie_sensitivity: float = 0.0    # Plus élevé = plus restrictif sur les calories

    def __post_init__(self):
        """Validation et ajustements automatiques du profil"""

        # Ajustements automatiques selon l'âge
        if self.age_group == AgeGroup.CHILD:
            # Les enfants sont plus sensibles au sucre et sodium
            self.sugar_sensitivity = max(self.sugar_sensitivity, 0.3)
            self.sodium_sensitivity = max(self.sodium_sensitivity, 0.2)
            # Alcool strictement interdit pour les enfants
            self.alcohol_allowed = False

        elif self.age_group == AgeGroup.TEENAGER:
            # Adolescents : restriction alcool et attention au sucre
            self.alcohol_allowed = False
            self.sugar_sensitivity = max(self.sugar_sensitivity, 0.1)

        elif self.age_group == AgeGroup.SENIOR:
            # Seniors : plus sensibles au sodium et aux calories
            self.sodium_sensitivity = max(self.sodium_sensitivity, 0.2)
            self.calorie_sensitivity = max(self.calorie_sensitivity, 0.1)

        # Ajustements selon les objectifs de santé
        if HealthGoal.LOSE_WEIGHT in self.health_goals:
            self.calorie_sensitivity = max(self.calorie_sensitivity, 0.3)
            self.sugar_sensitivity = max(self.sugar_sensitivity, 0.2)

        if HealthGoal.REDUCE_SUGAR in self.health_goals:
            self.sugar_sensitivity = max(self.sugar_sensitivity, 0.5)

        if DietaryRestriction.DIABETIC in self.dietary_restrictions:
            self.sugar_sensitivity = max(self.sugar_sensitivity, 0.8)
            self.max_sugar_tolerance = min(self.max_sugar_tolerance or 5.0, 5.0)

        if DietaryRestriction.LOW_SODIUM in self.dietary_restrictions:
            self.sodium_sensitivity = max(self.sodium_sensitivity, 0.6)
            self.max_sodium_tolerance = min(self.max_sodium_tolerance or 0.3, 0.3)

    def get_alcohol_restriction_level(self) -> float:
        """Retourne le niveau de restriction sur l'alcool (0.0 = autorisé, 1.0 = interdit)"""
        if not self.alcohol_allowed:
            return 1.0

        # Même si autorisé, peut être restreint selon l'âge ou les objectifs
        restriction = 0.0

        if self.age_group in [AgeGroup.CHILD, AgeGroup.TEENAGER]:
            restriction = 1.0
        elif HealthGoal.IMPROVE_HEALTH in self.health_goals:
            restriction = 0.8
        elif HealthGoal.LOSE_WEIGHT in self.health_goals:
            restriction = 0.6

        return restriction

    def get_sugar_penalty_multiplier(self) -> float:
        """Retourne le multiplicateur de pénalité pour le sucre"""
        base_multiplier = 1.0
        return base_multiplier + self.sugar_sensitivity

    def get_sodium_penalty_multiplier(self) -> float:
        """Retourne le multiplicateur de pénalité pour le sodium"""
        base_multiplier = 1.0
        return base_multiplier + self.sodium_sensitivity

    def get_calorie_penalty_multiplier(self) -> float:
        """Retourne le multiplicateur de pénalité pour les calories"""
        base_multiplier = 1.0
        return base_multiplier + self.calorie_sensitivity

    def check_allergies(self, product_categories: List[str], product_ingredients: List[str] = None) -> List[str]:
        """Vérifie les allergies dans un produit et retourne la liste des allergènes détectés"""
        detected_allergens = []

        if not self.allergies:
            return detected_allergens

        # Vérifier dans les catégories
        for category in product_categories:
            for allergen in self.allergies:
                if allergen.lower() in category.lower():
                    detected_allergens.append(allergen)

        # Vérifier dans les ingrédients si disponibles
        if product_ingredients:
            for ingredient in product_ingredients:
                for allergen in self.allergies:
                    if allergen.lower() in ingredient.lower():
                        detected_allergens.append(allergen)

        return list(set(detected_allergens))  # Enlever les doublons

    def check_dietary_restrictions(self, product_categories: List[str]) -> List[DietaryRestriction]:
        """Vérifie les restrictions alimentaires violées par un produit"""
        violations = []

        for restriction in self.dietary_restrictions:
            if restriction == DietaryRestriction.VEGETARIAN:
                if any(keyword in cat.lower() for cat in product_categories
                      for keyword in ['meat', 'fish', 'seafood', 'poultry']):
                    violations.append(restriction)

            elif restriction == DietaryRestriction.VEGAN:
                if any(keyword in cat.lower() for cat in product_categories
                      for keyword in ['meat', 'fish', 'seafood', 'poultry', 'dairy', 'eggs', 'honey']):
                    violations.append(restriction)

            elif restriction == DietaryRestriction.GLUTEN_FREE:
                if any(keyword in cat.lower() for cat in product_categories
                      for keyword in ['wheat', 'gluten', 'bread', 'pasta', 'cereal']):
                    violations.append(restriction)

            elif restriction == DietaryRestriction.LACTOSE_FREE:
                if any(keyword in cat.lower() for cat in product_categories
                      for keyword in ['dairy', 'milk', 'cheese', 'yogurt']):
                    violations.append(restriction)

            elif restriction == DietaryRestriction.HALAL:
                if any(keyword in cat.lower() for cat in product_categories
                      for keyword in ['pork', 'alcohol', 'wine', 'beer']):
                    violations.append(restriction)

        return violations

# Profils prédéfinis pour différents types d'utilisateurs

def create_child_profile(name: str, allergies: List[str] = None) -> UserProfile:
    """Crée un profil pour enfant (3-12 ans)"""
    return UserProfile(
        name=name,
        age_group=AgeGroup.CHILD,
        activity_level=ActivityLevel.MODERATE,
        dietary_restrictions=[],
        allergies=allergies or [],
        health_goals=[HealthGoal.IMPROVE_HEALTH],
        alcohol_allowed=False,
        max_sugar_tolerance=15.0,
        max_sodium_tolerance=0.5
    )

def create_teenager_profile(name: str, health_goals: List[HealthGoal] = None) -> UserProfile:
    """Crée un profil pour adolescent (13-17 ans)"""
    return UserProfile(
        name=name,
        age_group=AgeGroup.TEENAGER,
        activity_level=ActivityLevel.ACTIVE,
        dietary_restrictions=[],
        allergies=[],
        health_goals=health_goals or [HealthGoal.MAINTAIN_WEIGHT],
        alcohol_allowed=False,
        max_sugar_tolerance=20.0
    )

def create_adult_profile(name: str, **kwargs) -> UserProfile:
    """Crée un profil pour adulte avec options personnalisables"""
    defaults = {
        'age_group': AgeGroup.ADULT,
        'activity_level': ActivityLevel.MODERATE,
        'dietary_restrictions': [],
        'allergies': [],
        'health_goals': [HealthGoal.MAINTAIN_WEIGHT],
        'alcohol_allowed': True
    }
    defaults.update(kwargs)

    return UserProfile(name=name, **defaults)

def create_senior_profile(name: str, health_conditions: List[str] = None) -> UserProfile:
    """Crée un profil pour senior (65+ ans)"""
    restrictions = []
    health_goals = [HealthGoal.IMPROVE_HEALTH]

    # Ajuster selon les conditions de santé
    if health_conditions:
        if 'diabetes' in health_conditions:
            restrictions.append(DietaryRestriction.DIABETIC)
            health_goals.append(HealthGoal.REDUCE_SUGAR)
        if 'hypertension' in health_conditions:
            restrictions.append(DietaryRestriction.LOW_SODIUM)

    return UserProfile(
        name=name,
        age_group=AgeGroup.SENIOR,
        activity_level=ActivityLevel.LIGHT,
        dietary_restrictions=restrictions,
        allergies=[],
        health_goals=health_goals,
        alcohol_allowed=False,
        max_sugar_tolerance=10.0,
        max_sodium_tolerance=0.3
    )
