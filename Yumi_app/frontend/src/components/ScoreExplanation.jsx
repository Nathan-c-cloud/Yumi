import React, { useState } from 'react';
import { Info, ChevronDown, ChevronUp } from 'lucide-react';
import { Button } from '@/components/ui/button';

const ScoreExplanation = ({ yumiScore, warnings = [] }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const getScoreExplanation = (score) => {
    if (score >= 80) {
      return {
        title: "Excellent choix ! 🌟",
        description: "Ce produit correspond parfaitement à vos préférences et objectifs nutritionnels.",
        tips: [
          "Vous pouvez le consommer en toute confiance",
          "Il s'intègre parfaitement dans une alimentation équilibrée",
          "Bravo pour ce choix santé !"
        ]
      };
    } else if (score >= 60) {
      return {
        title: "Bon choix ! 👍",
        description: "Ce produit convient bien à vos besoins, avec quelques points d'attention mineurs.",
        tips: [
          "C'est un produit de qualité pour votre profil",
          "Peut être consommé régulièrement sans souci",
          "Quelques petits ajustements pourraient l'améliorer"
        ]
      };
    } else if (score >= 40) {
      return {
        title: "Choix modéré 🤔",
        description: "Ce produit peut convenir occasionnellement, mais il existe probablement de meilleures alternatives.",
        tips: [
          "Parfait pour un plaisir de temps en temps",
          "Essayez de l'équilibrer avec d'autres aliments plus adaptés",
          "Nous avons peut-être des suggestions d'alternatives"
        ]
      };
    } else {
      return {
        title: "Attention aux détails 💡",
        description: "Ce produit présente quelques incompatibilités avec vos préférences ou objectifs.",
        tips: [
          "Pas d'interdiction, mais à consommer avec modération",
          "Vérifiez les ingrédients qui vous préoccupent",
          "Découvrez nos alternatives plus adaptées à votre profil"
        ]
      };
    }
  };

  const explanation = getScoreExplanation(yumiScore);

  const getWarningExplanations = (warnings) => {
    return warnings.map(warning => {
      if (warning.includes('halal') || warning.includes('porc')) {
        return "🕌 Ce produit contient des ingrédients non halal selon vos préférences";
      }
      if (warning.includes('végétarien') || warning.includes('viande')) {
        return "🌱 Ce produit contient des ingrédients d'origine animale";
      }
      if (warning.includes('allergène') || warning.includes('allergie')) {
        return "⚠️ Ce produit contient des allergènes à éviter selon votre profil";
      }
      if (warning.includes('sucre') || warning.includes('diabète')) {
        return "🍯 Attention au taux de sucre pour vos objectifs santé";
      }
      if (warning.includes('sel') || warning.includes('sodium')) {
        return "🧂 Taux de sel élevé par rapport à vos objectifs";
      }
      if (warning.includes('calorie') || warning.includes('poids')) {
        return "⚖️ Produit plus calorique que recommandé pour vos objectifs";
      }
      return warning; // Fallback pour les warnings non catégorisés
    });
  };

  const friendlyWarnings = getWarningExplanations(warnings);

  return (
    <div className="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Info className="h-5 w-5 text-blue-600" />
          <span className="font-medium text-blue-800">Comprendre votre score</span>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setIsExpanded(!isExpanded)}
          className="text-blue-600 hover:text-blue-800"
        >
          {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </Button>
      </div>

      {isExpanded && (
        <div className="mt-4 space-y-4">
          <div>
            <h4 className="font-semibold text-gray-800 mb-2">{explanation.title}</h4>
            <p className="text-gray-600 text-sm mb-3">{explanation.description}</p>

            <div className="space-y-1">
              {explanation.tips.map((tip, index) => (
                <div key={index} className="flex items-start space-x-2">
                  <span className="text-green-500 mt-1">•</span>
                  <span className="text-sm text-gray-700">{tip}</span>
                </div>
              ))}
            </div>
          </div>

          {friendlyWarnings.length > 0 && (
            <div className="border-t border-blue-200 pt-3">
              <h5 className="font-medium text-gray-800 mb-2">Points d'attention personnalisés :</h5>
              <div className="space-y-1">
                {friendlyWarnings.map((warning, index) => (
                  <div key={index} className="flex items-start space-x-2">
                    <span className="text-orange-500 mt-1">•</span>
                    <span className="text-sm text-gray-700">{warning}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="border-t border-blue-200 pt-3">
            <div className="flex items-center space-x-2 mb-2">
              <span className="text-sm font-medium text-gray-800">Votre score Yumi :</span>
              <div className="flex items-center space-x-1">
                <div className="w-12 h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-300"
                    style={{
                      width: `${yumiScore}%`,
                      backgroundColor: yumiScore >= 80 ? '#22C55E' :
                                     yumiScore >= 60 ? '#FACC15' :
                                     yumiScore >= 40 ? '#F97316' : '#EF4444'
                    }}
                  />
                </div>
                <span className="text-sm font-semibold">{yumiScore}/100</span>
              </div>
            </div>
            <p className="text-xs text-gray-500">
              Ce score est personnalisé selon vos préférences alimentaires, objectifs de santé et restrictions.
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default ScoreExplanation;
