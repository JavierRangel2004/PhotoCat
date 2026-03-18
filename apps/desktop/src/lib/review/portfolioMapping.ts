const SAFE_MAPPINGS: Record<string, string> = {
  "Events & Music": "concert",
  "Food & Product": "product",
  "Nature & Landscape": "nature",
};

const DEFAULT_AMBIGUOUS_MAPPINGS: Record<string, string> = {
  "Branding & Portrait": "portraits",
  "Street Documentary": "city",
  "Travel & Architecture": "travel-cityscape",
};

const EXCLUDED_GENRES = new Set([
  "Wedding Photography",
  "Other Photography",
]);

const PORTFOLIO_GROUPS: Record<string, string> = {
  portraits: "branding",
  product: "branding",
  concert: "events",
  nature: "author-archive",
  city: "author-archive",
  "travel-cityscape": "author-archive",
  exclude: "exclude",
};

export const PORTFOLIO_CATEGORIES = [
  "portraits",
  "concert",
  "city",
  "nature",
  "product",
  "travel-cityscape",
] as const;

export const PORTFOLIO_CATEGORY_OPTIONS = [...PORTFOLIO_CATEGORIES, "exclude"];

export type PortfolioCategory = (typeof PORTFOLIO_CATEGORIES)[number] | "exclude";

export type PortfolioMapping = {
  portfolioCategory: PortfolioCategory;
  portfolioGroup: string;
  exportInclude: boolean;
  portfolioNeedsReview: boolean;
  portfolioMappingSource: "auto" | "user" | "default-exclude";
};

function isPortfolioCategory(value: string): value is PortfolioCategory {
  return value === "exclude" || PORTFOLIO_CATEGORIES.includes(value as (typeof PORTFOLIO_CATEGORIES)[number]);
}

export function resolvePortfolioMapping(effectiveGenre: string, userPortfolioCategory = ""): PortfolioMapping {
  const normalizedOverride = userPortfolioCategory.trim().toLowerCase();

  let portfolioCategory: PortfolioCategory = "exclude";
  let portfolioMappingSource: PortfolioMapping["portfolioMappingSource"] = "default-exclude";
  let portfolioNeedsReview = false;

  if (normalizedOverride && isPortfolioCategory(normalizedOverride)) {
    portfolioCategory = normalizedOverride;
    portfolioMappingSource = "user";
  } else if (effectiveGenre in SAFE_MAPPINGS) {
    portfolioCategory = SAFE_MAPPINGS[effectiveGenre] as PortfolioCategory;
    portfolioMappingSource = "auto";
  } else if (effectiveGenre in DEFAULT_AMBIGUOUS_MAPPINGS) {
    portfolioCategory = DEFAULT_AMBIGUOUS_MAPPINGS[effectiveGenre] as PortfolioCategory;
    portfolioMappingSource = "auto";
    portfolioNeedsReview = true;
  } else {
    portfolioNeedsReview = true;
  }

  return {
    portfolioCategory,
    portfolioGroup: PORTFOLIO_GROUPS[portfolioCategory] ?? "exclude",
    exportInclude: portfolioCategory !== "exclude",
    portfolioNeedsReview,
    portfolioMappingSource,
  };
}

export function computeDestRelpath(portfolioCategory: PortfolioCategory, filename: string, effectiveGenre = "") {
  if (portfolioCategory === "exclude") {
    return `excluded/${effectiveGenre || "unknown"}/${filename}`;
  }
  return `photos/${portfolioCategory}/${filename}`;
}

export function deriveReviewItemOrganizeFields(item: {
  effectiveGenre: string;
  userPortfolioCategory: string;
  filename: string;
}) {
  const mapping = resolvePortfolioMapping(item.effectiveGenre, item.userPortfolioCategory);
  return {
    portfolioCategory: mapping.portfolioCategory,
    portfolioGroup: mapping.portfolioGroup,
    exportInclude: mapping.exportInclude,
    destRelpath: computeDestRelpath(mapping.portfolioCategory, item.filename, item.effectiveGenre),
    portfolioNeedsReview: mapping.portfolioNeedsReview,
    portfolioMappingSource: mapping.portfolioMappingSource,
  };
}

export function joinOutputPath(outputDir: string, destRelpath: string) {
  const trimmedRoot = outputDir.trim().replace(/[\\/]+$/, "");
  if (!trimmedRoot) {
    return destRelpath;
  }
  return `${trimmedRoot}\\${destRelpath.replaceAll("/", "\\")}`;
}
