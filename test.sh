#!/bin/sh

# ------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------
# Votre nom correct (utilisé pour les commits réécrits)
CORRECT_NAME="Florent" 
# Votre adresse e-mail correcte et associée à GitHub
CORRECT_EMAIL="florentpuy@proton.me"

# Cette variable est laissée vide. Le script corrigera tous les commits
# dont l'adresse n'est PAS l'adresse CORRECT_EMAIL.
# Si vous aviez une ancienne adresse spécifique, vous pourriez la mettre ici:
# OLD_EMAIL="autre_email@incorrect.com"
# ------------------------------------------------------------

# Assurez-vous d'abord que l'identité globale est correcte pour les futurs commits
git config --global user.name "$CORRECT_NAME"
git config --global user.email "$CORRECT_EMAIL"

echo "Démarrage de la réécriture de l'historique..."
echo "Les commits qui ne sont PAS de '$CORRECT_EMAIL' seront attribués à '$CORRECT_NAME <$CORRECT_EMAIL>'."

# L'outil filter-branch modifie l'historique commit par commit.
git filter-branch --env-filter '
an="$GIT_AUTHOR_NAME"
am="$GIT_AUTHOR_EMAIL"
cn="$GIT_COMMITTER_NAME"
cm="$GIT_COMMITTER_EMAIL"

# ------------------------------------------------------------
# Logique de Correction: Si l adresse de l auteur ou du commiteur est différente
# de l adresse correcte, elle est corrigée.
# ------------------------------------------------------------

if [ "$GIT_AUTHOR_EMAIL" != "$CORRECT_EMAIL" ]
then
    an="'"$CORRECT_NAME"'"
    am="'"$CORRECT_EMAIL"'"
fi

if [ "$GIT_COMMITTER_EMAIL" != "$CORRECT_EMAIL" ]
then
    cn="'"$CORRECT_NAME"'"
    cm="'"$CORRECT_EMAIL"'"
fi

export GIT_AUTHOR_NAME="$an"
export GIT_AUTHOR_EMAIL="$am"
export GIT_COMMITTER_NAME="$cn"
export GIT_COMMITTER_EMAIL="$cm"
' --tag-name-filter cat -- --branches --tags

echo "Réécriture de l'historique local terminée."
