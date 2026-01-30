export interface ExampleCourse {
  name: string;
  description: string;
  yaml: string;
}

export const EXAMPLES: ExampleCourse[] = [
  {
    name: "Introduction to Pandas",
    description: "8-item course with branching prerequisites",
    yaml: `domain:
  name: "Introduction to Pandas"
  description: "Foundational skills for data manipulation with pandas"
  items:
    - id: "import"
      label: "Importing pandas and reading data"
    - id: "series"
      label: "Understanding pandas Series"
    - id: "dataframe"
      label: "Understanding DataFrames"
    - id: "indexing"
      label: "Indexing and selecting data"
    - id: "filtering"
      label: "Boolean indexing and filtering"
    - id: "groupby"
      label: "GroupBy operations"
    - id: "merge"
      label: "Merging and joining DataFrames"
    - id: "pivot"
      label: "Pivot tables and reshaping"

prerequisites:
  edges:
    - ["import", "series"]
    - ["import", "dataframe"]
    - ["series", "indexing"]
    - ["dataframe", "indexing"]
    - ["indexing", "filtering"]
    - ["indexing", "groupby"]
    - ["dataframe", "merge"]
    - ["indexing", "merge"]
    - ["groupby", "pivot"]
    - ["filtering", "pivot"]
`,
  },
  {
    name: "Linear Chain",
    description: "5-item total order (a -> b -> c -> d -> e)",
    yaml: `domain:
  name: "Linear Chain"
  description: "A simple total order with 5 items"
  items:
    - id: "a"
      label: "Foundations"
    - id: "b"
      label: "Core concepts"
    - id: "c"
      label: "Intermediate skills"
    - id: "d"
      label: "Advanced topics"
    - id: "e"
      label: "Mastery"

prerequisites:
  edges:
    - ["a", "b"]
    - ["b", "c"]
    - ["c", "d"]
    - ["d", "e"]
`,
  },
  {
    name: "Diamond Lattice",
    description: "4-item diamond (a -> {b, c} -> d)",
    yaml: `domain:
  name: "Diamond Lattice"
  description: "A diamond prerequisite structure with two parallel branches"
  items:
    - id: "a"
      label: "Foundation"
    - id: "b"
      label: "Branch 1"
    - id: "c"
      label: "Branch 2"
    - id: "d"
      label: "Capstone"

prerequisites:
  edges:
    - ["a", "b"]
    - ["a", "c"]
    - ["b", "d"]
    - ["c", "d"]
`,
  },
  {
    name: "Data Science Foundations",
    description: "12-item domain with multiple branches",
    yaml: `domain:
  name: "Data Science Foundations"
  description: "A 12-item domain covering core data science skills with branching prerequisites"
  items:
    - id: "python"
      label: "Python programming basics"
    - id: "numpy"
      label: "NumPy arrays and operations"
    - id: "pandas"
      label: "Pandas DataFrames"
    - id: "linalg"
      label: "Linear algebra concepts"
    - id: "stats"
      label: "Descriptive statistics"
    - id: "cleaning"
      label: "Data cleaning techniques"
    - id: "merging"
      label: "Merging and joining datasets"
    - id: "ml_basics"
      label: "Machine learning fundamentals"
    - id: "hypothesis"
      label: "Hypothesis testing"
    - id: "eda"
      label: "Exploratory data analysis"
    - id: "regression"
      label: "Linear regression"
    - id: "classification"
      label: "Classification algorithms"

prerequisites:
  edges:
    - ["python", "numpy"]
    - ["python", "pandas"]
    - ["numpy", "linalg"]
    - ["numpy", "stats"]
    - ["pandas", "cleaning"]
    - ["pandas", "merging"]
    - ["linalg", "ml_basics"]
    - ["stats", "ml_basics"]
    - ["stats", "hypothesis"]
    - ["cleaning", "eda"]
    - ["merging", "eda"]
    - ["ml_basics", "regression"]
    - ["ml_basics", "classification"]
`,
  },
];
