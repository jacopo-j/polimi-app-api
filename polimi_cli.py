#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import os
import re
from getpass import getpass
import json
import keyring


# ID relativo all'app per Android
CLIENT_ID = "9978142015"

# Segreto del client. Per motivi di sicurezza non viene incluso in
# questo repository, ma si può ricavare facilmente dall'applicazione.
CLIENT_SECRET = os.environ["POLIMI_CLIENT_SECRET"]

# URL autenticazione
OAUTH_AUTH_URL = "https://oauthidp.polimi.it/oauthidp/oauth2/auth"
OAUTH_TOKEN_URL = "https://oauthidp.polimi.it/oauthidp/oauth2/token"
AUNICALOGIN_URL = "https://aunicalogin.polimi.it"

# URL vari
BASE_API_URL = "https://m.servizionline.polimi.it/info-didattica"
CAREERS_URL = "/rest/polimimobile/personaCarriere"
STUDYPLAN_URL = "/rest/polimimobile/studente/elencoRighePiano/{}"
TEACHING_URL = "/rest/polimimobile/studente/dettaglioRigaPiano/{}"

# REGEX vari
LOGIN_PATH_MATCH = r'<form.*?action="(.*?)"'
SUCCESS_CODE_MATCH = r"<title>Success code=(.*?)</title>"

# Dati stampabili
USER_INFO_PRINT = ("\nCodice persona: {person_code}\n"
                   "Cognome:        {last_name}\n"
                   "Nome:           {first_name}\n")
CAREER_INFO_PRINT = ("Matricola {mat_number}: tipo anagrafica: {person_type}\n"
                     "                  tipo carriera: {career_type}\n"
                     "                  stato carriera: {career_status}\n")
STUDYPLAN_PRINT = ("\nMatricola:       {mat_number}\n"
                   "Corso di laurea: {program}\n"
                   "Tipo CdL:        {type}\n"
                   "Anno accademico: {year}\n"
                   "Piano approvato: {approved}\n"
                   "Media:           {avg}\n"
                   "CFU superati:    {cfu}\n")
DONE_TEACHING_PRINT = ("{name}\n"
                       "    Anno accademico: {acc_year}\n"
                       "    Periodo: {period}\n"
                       "    Lingua: {language}\n"
                       "    Stato: {status}\n"
                       "    Data esame: {date}\n"
                       "    Voto: {vote}\n")
PART_TEACHING_PRINT = ("{name}\n"
                       "    Anno accademico: {acc_year}\n"
                       "    Periodo: {period}\n"
                       "    Lingua: {language}\n"
                       "    Stato: {status}\n"
                       "    Voto: {vote}\n")
NOTD_TEACHING_PRINT = ("{name}\n"
                       "    Anno accademico: {acc_year}\n"
                       "    Periodo: {period}\n"
                       "    Lingua: {language}\n"
                       "    Stato: {status}\n")


class PoliMiAccount:

    def __init__(self, person_code):
        self.person_code = str(person_code)
        self._session = requests.Session()
        self._access_token, self._refresh_token = self._get_tokens()

    def _get_new_tokens(self):
        res = self._session.get(
            OAUTH_AUTH_URL,
            params={"access_type": "offline",
                    "client_id": CLIENT_ID,
                    "redirect_uri": "urn:ietf:wg:oauth:2.0:oob",
                    "response_type": "code",
                    "scope": "openid 865",
                    "lang": "it"})
        login_path = re.findall(LOGIN_PATH_MATCH, res.text)[0]
        while True:
            res = self._session.post(
                AUNICALOGIN_URL + login_path,
                data={"login": self.person_code,
                      "password": getpass("Password: "),
                      "evn_conferma": ""})
            try:
                success_code = re.findall(SUCCESS_CODE_MATCH, res.text)[0]
                break
            except IndexError:
                print("Autenticazione fallita!\n")
        res = self._session.post(
            OAUTH_TOKEN_URL,
            data={"code": success_code,
                  "grant_type": "authorization_code",
                  "redirect_uri": "urn:ietf:wg:oauth:2.0:oob",
                  "scope": "openid 865",
                  "client_id": CLIENT_ID,
                  "client_secret": CLIENT_SECRET})
        tokens = res.json()
        keyring.set_password(
            "polimi_access_token",
            self.person_code,
            tokens["access_token"])
        keyring.set_password(
            "polimi_refresh_token",
            self.person_code,
            tokens["refresh_token"])
        return tokens

    def _get_tokens(self, force_renew=False):
        if force_renew:
            new_tokens = self._get_new_tokens()
            return (new_tokens["access_token"], new_tokens["refresh_token"])
        access_token = keyring.get_password(
            "polimi_access_token",
            self.person_code)
        refresh_token = keyring.get_password(
            "polimi_refresh_token",
            self.person_code)
        if any(x is None for x in (access_token, refresh_token)):
            return self._get_tokens(force_renew=True)
        return (access_token, refresh_token)

    def get_user_info(self):
        res = self._session.get(
            BASE_API_URL + CAREERS_URL,
            headers={"access_token": self._access_token,
                     "al_id_srv": "865",
                     "lang": "it"})
        data = res.json()
        if ("code" in data) and (data["code"] == "3000"):
            self._access_token, self._refresh_token = self._get_tokens(True)
            return self.get_user_info()
        output = {"person_code": data["codice_persona"],
                  "last_name": data["cognome"],
                  "first_name": data["nome"],
                  "default_mat": data["matricola_preferita"],
                  "careers": []}
        for car in data["collCarriere"]:
            output["careers"].append({"career_type": car["tipo_carriera_desc"],
                                      "person_type": car["tipo_anagrafica_desc"],
                                      "career_status": car["stato_carriera_desc"],
                                      "mat_number": car["matricola"]})
        return output

    def print_user_info(self):
        user_info = self.get_user_info()
        print(USER_INFO_PRINT.format(**user_info))
        for car in user_info["careers"]:
            print(CAREER_INFO_PRINT.format(**car))

    def get_studyplan(self, mat_number=None):
        if (mat_number is None):
            mat_number = self.get_user_info()["default_mat"]
        res = self._session.get(
            BASE_API_URL + STUDYPLAN_URL.format(mat_number),
            headers={"access_token": self._access_token,
                     "al_id_srv": "865",
                     "lang": "it"})
        data = res.json()
        if ("code" in data) and (data["code"] == "3000"):
            self._access_token, self._refresh_token = self._get_tokens(True)
            return self.get_studyplan()
        output = {"mat_number": data["matricola"],
                  "approved": data["approvato"],
                  "year": data["aa_val"],
                  "program": data["nome_cdl"],
                  "type": data["desc_tipo_corso"],
                  "avg": data["media"],
                  "cfu": data["cfu_superati"],
                  "teachings": []}
        for t in data["collInsegnamenti"]:
            output["teachings"].append({"period": t["desc_erogazione"],
                                        "status": t["desc_stato_esame"],
                                        "acc_year": t["aa_freq"],
                                        "name": t["n_insegn"],
                                        "language": t["lingua_erogazione"],
                                        "date": t["data_esame"] if "data_esame" in t else None,
                                        "vote": t["voto_esame"] if "voto_esame" in t else None})
        return output

    def print_studyplan(self, mat_number=None):
        studyplan = self.get_studyplan(mat_number)
        print(STUDYPLAN_PRINT.format(**studyplan))
        for t in studyplan["teachings"]:
            if (t["date"] is not None) and (t["vote"] is not None):
                print(DONE_TEACHING_PRINT.format(**t))
            elif (t["vote"] is not None):
                print(PART_TEACHING_PRINT.format(**t))
            else:
                print(NOTD_TEACHING_PRINT.format(**t))


