import pandas as pd
import numpy as np
from sklearn import metrics
from sklearn.ensemble import RandomForestClassifier, AdaBoostClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
from sklearn.model_selection import cross_val_score
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.naive_bayes import GaussianNB
from sklearn import svm
from sklearn.tree import DecisionTreeClassifier
import pandas as pd

def train_model(model,X,y):
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    if model=='RF':
        print("Random Forest")
        clf = RandomForestClassifier(random_state=42,n_estimators=100)
    elif model=='NB':
        print("Naive Bayes")
        clf=GaussianNB()
    elif model=='SVM':
        print("SVM")
        clf = svm.SVC(kernel='rbf',gamma='auto')
    elif model=='LR':
        print("LR")
        clf = LogisticRegression(solver='liblinear')#'liblinear', 'newton-cg', 'lbfgs', 'sag', 'saga'
    elif model=='KNN':
        print("KNN")
        clf=KNeighborsClassifier(n_neighbors=3)
    elif model == 'AdaBoost':
        print("AdaBoost")
        clf=AdaBoostClassifier(n_estimators=100, random_state=0)
    elif model=='DT':
        print("Decision Tree")
        clf = DecisionTreeClassifier(random_state=0)

    clf.fit(X_train,y_train)
    # if model=='RF':
    #     print("feature_importances_")
    #     print(clf.feature_importances_)
    # print("train accuracy: %0.3f" % clf.score(X_train, y_train))
    # print("RF test accuracy: %0.3f" % clf.score(X_test, y_test))

    y_pre = clf.predict((X_test))
    # print("=== Classification Report ===")
    # print(classification_report(y_test, y_pre))

    cv_score = cross_val_score(clf, X, y, cv=10, scoring='roc_auc')

    print("Mean AUC Score: %0.3f" % cv_score.mean())
    print("accuracy score: %0.3f" % metrics.accuracy_score(y_test, y_pre))
    print("precision score: %0.3f" % metrics.precision_score(y_test, y_pre, average='micro'))
    print("recall score: %0.3f"%metrics.recall_score(y_test, y_pre, average='micro'))
    print("f1 score: %0.3f" % metrics.f1_score(y_test, y_pre, average='weighted'))

    scores=[cv_score.mean(),
            metrics.accuracy_score(y_test, y_pre),
            metrics.precision_score(y_test, y_pre, average='micro'),
            metrics.recall_score(y_test, y_pre, average='micro'),
            metrics.f1_score(y_test, y_pre, average='weighted')]

    print("***********************************************")
    return scores


from sklearn.neighbors import KNeighborsClassifier


# rfc_cv_score = cross_val_score(rfc, X, y, cv=10, scoring='roc_auc')
# print("=== Confusion Matrix ===")
# print(confusion_matrix(y_test, rfc_predict))
# print('\n')
# print("=== Classification Report ===")
# print(classification_report(y_test, rfc_predict))
# print('\n')
# print("=== All AUC Scores ===")
# print(rfc_cv_score)
# print('\n')
# print("=== Mean AUC Score ===")
# print("Mean AUC Score - Random Forest: ", rfc_cv_score.mean())


def main():
    train = pd.read_csv('test_2.csv')
    label = 'label'
    id_col = 'id'
    username_col = 'username'
    print(train[label].value_counts())

    x_columns = [x for x in train.columns if x not in [label, id_col, username_col]]
    X = train[x_columns]
    X = np.nan_to_num(X)
    y = train[label]
    dict_scores={}
    print("***********************************************")
    for i in ['NB','LR','SVM','RF','KNN','AdaBoost','DT']:
        dict_scores[i]=train_model(i,X,y)

    print(dict_scores)
    draw(dict_scores)

def draw(dict):
    name_list=['Mean AUC','accuracy','precision','recall','f1']
    x = list(range(len(dict['NB'])))
    total_width, n = 0.8, 7
    width = total_width / n
    plt.bar(x, dict['NB'], width=width, label='NB', )
    for i in range(len(x)):
        x[i] = x[i] + width
    plt.bar(x, dict['LR'], width=width, label='LR')
    for i in range(len(x)):
        x[i] = x[i] + width
    plt.bar(x, dict['SVM'], width=width, label='SVM', tick_label=name_list)
    for i in range(len(x)):
        x[i] = x[i] + width
    plt.bar(x, dict['RF'], width=width, label='RF')
    for i in range(len(x)):
        x[i] = x[i] + width
    plt.bar(x, dict['KNN'], width=width, label='KNN')
    for i in range(len(x)):
        x[i] = x[i] + width
    plt.bar(x, dict['AdaBoost'], width=width, label='AdaBoost')
    for i in range(len(x)):
        x[i] = x[i] + width
    plt.bar(x, dict['DT'], width=width, label='DT')
    plt.title("实验结果")
    plt.legend()
    plt.show()

if __name__=='__main__':
    main()












