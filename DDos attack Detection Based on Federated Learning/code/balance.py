import pandas as pd
import os
from imblearn.under_sampling import RandomUnderSampler
from imblearn.over_sampling import SMOTE, RandomOverSampler


def ros(dataset):
    r = RandomOverSampler(random_state=0)
    X, y = r.fit_resample(dataset.iloc[:, :-1], dataset.iloc[:, -1])
    new_dataset = pd.DataFrame(X)
    new_dataset['target'] = y
    return new_dataset


def smote(dataset):
    sm = SMOTE(random_state=42)
    X, y = sm.fit_resample(dataset.iloc[:, :-1], dataset.iloc[:, -1])
    new_dataset = pd.DataFrame(X)
    new_dataset['target'] = y
    return new_dataset


def rus(dataset):
    r = RandomUnderSampler(random_state=0)
    X, y = r.fit_resample(dataset.iloc[:, :-1], dataset.iloc[:, -1])
    new_dataset = pd.DataFrame(X)
    new_dataset['target'] = y
    return new_dataset



path1 = '.\\over_sampling\\'
path2 = '.\\under_sampling\\'
path3 = '.\\smote\\'
if not os.path.exists(path1):
    os.makedirs(path1)
    os.makedirs(path2)
    os.makedirs(path3)
print('Folders created.')



print('Datasets reading...')
client1 = pd.read_csv('dataset/client1_processed.csv')
#client2 = pd.read_csv('dataset/client2_processed.csv')
#client3 = pd.read_csv('dataset/client3_processed.csv')



print('Creating under sampling datasets...')
rus(client1).to_csv('./under_sampling/client1_processed.csv', index=False)
#rus(client2).to_csv('./under_sampling/client2_processed.csv', index=False)
#rus(client3).to_csv('./under_sampling/client3_processed.csv', index=False)



print('Creating smote datasets...')
smote(client1).to_csv('./smote/client1_processed.csv', index=False)
#smote(client2).to_csv('./smote/client2_processed.csv', index=False)
#smote(client3).to_csv('./smote/client3_processed.csv', index=False)




print('Creating over sampling datasets...')
ros(client1).to_csv('./over_sampling/client1_processed.csv', index=False)
#ros(client2).to_csv('./over_sampling/client2_processed.csv', index=False)
#ros(client3).to_csv('./over_sampling/client3_processed.csv', index=False)


print('All Done!')
