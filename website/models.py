import pandas as pd
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.impute import SimpleImputer
import os
from flask import jsonify, request

# Get the current directory of the main.py file
current_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the file path
file_path = os.path.join(current_dir, '..', 'DATASET_ONE.csv')  # Go one directory up to access TEST.csv

# Load the CSV file
data = pd.read_csv(file_path)

# Convert to DataFrame
df = pd.DataFrame(data)

# Convert categorical columns to string
categorical_features = [
    'study_hours', 'study_strategies', 'regular_study_schedule',
    'attendance_rate', 'class_participation', 'time_management_rating',
    'study_deadlines_frequency', 'motivation_level', 'engagement_level',
    'stress_frequency', 'coping_effectiveness', 'gender', 'mother_occupation', 'father_occupation'
]

df[categorical_features] = df[categorical_features].astype(str)

# Define columns for feature groups
socioeconomic_features = [
    'gender', 'age', 'mother_occupation', 'father_occupation',
    'mother_monthly_income', 'father_monthly_income', 'no_of_siblings'
]

academic_features = [
    'average_grade_g12', 'average_grade_first_year', 'grades_understanding_self',
    'grades_purposive_communication', 'grades_art_appreciation', 'grades_sts',
    'grades_environmental_science', 'grades_intermediate_programming',
    'grades_discrete_mathematics', 'grades_contemporary_world_with_peace_education',
    'grades_mathematics_in_the_modern_world', 'grades_introduction_computing',
    'grades_fundamentals_of_programming'
]

behavioral_features = [
    'study_hours', 'study_strategies', 'regular_study_schedule', 
    'attendance_rate', 'class_participation', 'time_management_rating', 
    'study_deadlines_frequency', 'motivation_level', 
    'engagement_level', 'stress_frequency', 'coping_effectiveness'
]

# Combine all features for training
numerical_features = [
    'age', 'no_of_siblings', 'mother_monthly_income', 'father_monthly_income'
] + academic_features  # Assuming these are numerical

# Define preprocessing
preprocessor = ColumnTransformer(
    transformers=[
        ('num', Pipeline(steps=[
            ('imputer', SimpleImputer(strategy='median')),
            ('scaler', StandardScaler())
        ]), numerical_features),

        ('cat', Pipeline(steps=[
            ('imputer', SimpleImputer(strategy='constant', fill_value='missing')),
            ('onehot', OneHotEncoder(handle_unknown='ignore'))
        ]), categorical_features)
    ])

# Model pipeline
model = Pipeline(steps=[
    ('preprocessor', preprocessor),
    ('classifier', LogisticRegression(max_iter=1000))
])

# Prepare data
X = df.drop('graduate_on_time', axis=1)
y = df['graduate_on_time']

# Train the model
model.fit(X, y)

# Extract feature names
def get_feature_names(column_transformer):
    feature_names = []
    for name, transformer, columns in column_transformer.transformers_:
        if name == 'num':
            feature_names.extend(columns)
        elif name == 'cat':
            feature_names.extend(transformer.named_steps['onehot'].get_feature_names_out(columns))
    return feature_names

# Get feature names
feature_names = get_feature_names(preprocessor)

# Get model coefficients
def get_feature_importance(model, feature_names):
    coef = model.named_steps['classifier'].coef_[0]
    feature_importance = pd.DataFrame({'Feature': feature_names, 'Coefficient': coef})
    return feature_importance

feature_importance = get_feature_importance(model, feature_names)

# Percentage of students graduating on time
total_students = len(df)
graduate_on_time_count = df['graduate_on_time'].sum()
percentage_graduating_on_time = (graduate_on_time_count / total_students) * 100

# Print the percentage of students graduating on time
#print(f"Percentage of Students Graduating on Time (DATASET): {percentage_graduating_on_time:.2f}%")

# Prepare the data for predictions
students_data = df.drop('graduate_on_time', axis=1).to_dict(orient='records')

# Now you can iterate over students_data
for index, input_features in enumerate(students_data):
    # Convert input features to a DataFrame for prediction
    input_df = pd.DataFrame([input_features])  # Create a DataFrame with one row

    # Make a prediction using the DataFrame
    prediction = model.predict(input_df)  # No need to convert to 2D array

    remark = "Graduate on Time" if prediction[0] == 1 else "Not Graduate on Time"

    main_factor_str = "No significant factors identified"  # Placeholder for clarity


# Set display options to show all rows
pd.set_option('display.max_rows', None)
pd.set_option('display.width', None)

# Display feature importances
print("Feature Importances:\n", feature_importance)

# Check for missing values after preprocessing
print("Missing values after preprocessing:\n", df.isnull().sum())
