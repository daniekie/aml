import pandas as pd
import xgboost as xgb
import numpy as np
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import Normalizer, StandardScaler, RobustScaler
from sklearn.impute import SimpleImputer
from sklearn.neighbors import LocalOutlierFactor

# Import data
sample = pd.read_csv('raw/sample.csv')
X_test = pd.read_csv('raw/X_test.csv', index_col='id')
X_train = pd.read_csv('raw/X_train.csv', index_col='id')
y_train = pd.read_csv('raw/y_train.csv', index_col='id')
print('Data shape before outlier detection', X_train.shape, y_train.shape)


# Outlier detection
loc = LocalOutlierFactor()
outliers = loc.fit_predict(X_train)
# select all rows that are not outliers
mask = outliers != -1
X_train, y_train = X_train[mask, :], y_train[mask]
# summarize the shape of the updated training dataset
print('Training data shape', X_train.shape, y_train.shape)


# Reduce Data for debugging
if 1:
    [X_train, a, y_train, b] = train_test_split(X_train, y_train, test_size=0.99)
    del a, b

# Inspect data
percent_missing = X_test.isnull().sum() * 100 / len(X_test)
missing_value_df = pd.DataFrame({'column_name': X_test.columns,
                                 'percent_missing': percent_missing})
missing_value_df.sort_values('percent_missing', inplace=True)
# X_train is missing 3%-10% of the values


# Create pipeline
pipe = Pipeline([
    # the scale stage is populated by the param_grid
    ('scale', 'passthrough'),
    ('impute', SimpleImputer()),
    ('estimation', xgb.XGBRegressor())
])


# Specify parameters to be searched over
param_grid = [
     {
        'scale': [Normalizer(), StandardScaler(), RobustScaler()],
        'impute__strategy': ['mean', 'median', 'most_frequent'],
        'estimation__max_depth':[6],  # [2, 6, 8],
        'estimation__gamma': [0],  # [0, 2, 8],
        'estimation__min_child_weight': [1]  # [1, 4, 8]
        }
]


# Gridsearch
search = GridSearchCV(pipe, param_grid=param_grid, n_jobs=-1, scoring='r2')
print("Starting Gridsearch")
search.fit(X_train, y_train)


# Evaluate Results
print("Best parameters set found on development set:")
print()
print('R2 score: ', search.best_score_)
print(search.best_params_)
print()
print("Grid scores on development set:")
print()
means = search.cv_results_['mean_test_score']
stds = search.cv_results_['std_test_score']
for mean, std, params in zip(means, stds, search.cv_results_['params']):
    print("%0.3f (+/-%0.03f) for %r"
          % (mean, std * 2, params))
print()


# Predict for test set
y_test = search.predict(X_test)
print()


# Save prediction
y_test = pd.DataFrame(y_test)
y_test.to_csv('prediction.csv', index_label='id', header=['y'], compression=None)
print('Results saved as prediction.csv')
