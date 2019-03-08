"""
Aplikacja do harmonogramowania transportu towarów dla trzech pojazdów
"""
import urllib.request

import sqlite3
import csv

import numpy as np
from math import exp

from tkinter import *
from tkinter import ttk
from tkinter.scrolledtext import *

import random
import webbrowser

import json
import urllib.request
from urllib.error import URLError


class Aplikacja:
    def __init__(self, master):
        self.master = master
        master.title("Harmonogramowanie transportu towarów dla floty pojazdów")

        # klucz api
        self.klucz_api = self.wczytaj_klucz_api("api_key.txt")

        # polaczenie i kursor do polączenia z bazą danych SQLite
        self.baza_polaczenie = sqlite3.connect('baza.db')
        self.kursor = self.baza_polaczenie.cursor()

        self.liczba_lokalizacji = self.inicjalizuj_baze_danych()

        self.lista_wspol, self.lista_lokalizacji = self.wczytaj_liste_miejsc()

        # określa liczbę miejsc do odwiedzenia
        self.liczba_miejsc_odwiedz = 10

        # określa listę pol miast do odwiedzenia
        self.lista_lok_miejsc = []

        self.punkt_start_tekst = "Podaj lokalizację początkową"
        self.napis_start = StringVar()
        self.napis_start.set(self.punkt_start_tekst)
        self.etykieta_start = Label(master, textvariable=self.napis_start)

        self.miejsca_tekst = "Podaj liczbę miejsc"
        self.napis_miejsca = StringVar()
        self.napis_miejsca.set(self.miejsca_tekst)
        self.etykieta_miejsca = Label(master, textvariable=self.napis_miejsca)

        self.lokal_tekst = "Podaj kolejne lokalizacje"
        self.napis_lokal = StringVar()
        self.napis_lokal.set(self.lokal_tekst)
        self.etykieta_lokal = Label(master, textvariable=self.napis_lokal)

        self.dodaj_tekst = "Wpisz nowe współrzędne"
        self.napis_dodaj = StringVar()
        self.napis_dodaj.set(self.dodaj_tekst)
        self.etykieta_dodaj = Label(master, textvariable=self.napis_dodaj)

        self.edytor_wsp = Entry(master, width=5)

        self.lista_lok_start = StringVar()
        self.lista_lok_start = ttk.Combobox(master, state='readonly', values=("Wrocław"))
        self.lista_lok_start.current(0)

        self.wybor_liczby_lok = StringVar
        self.wybor_liczby_lok = ttk.Combobox(master, state='readonly')
        self.wybor_liczby_lok['values'] = ["3", "4", "5", "6", "7", "8", "9", "10"]
        self.wybor_liczby_lok.current(7)

        self.okno_edycyjne = ScrolledText(master, width=60, height=20, font="Arial 10")

        self.przycisk_zmien = Button(master, text="Zmień liczbę miejsc", command=self.zmien_liczbe_miejsc)
        self.przycisk_wyznacz = Button(master, text="Wyznacz", command=self.uruchom)
        self.przycisk_wyczysc = Button(master, text="Wyczyść", command=self.wyczysc)
        self.przycisk_dodaj_wsp = Button(master, text="Dodaj", command=self.dodaj_nowe_wsp)

        self.etykieta_start.grid(row=0, column=0, columnspan=1, sticky=W + E)
        self.lista_lok_start.grid(row=0, column=1, columnspan=1)

        self.etykieta_miejsca.grid(row=1, column=0, columnspan=1, sticky=W + E)
        self.wybor_liczby_lok.grid(row=1, column=1, columnspan=2, sticky=W + E)
        self.przycisk_zmien.grid(row=2, column=1, columnspan=2)

        self.etykieta_lokal.grid(row=4, column=0, columnspan=1, sticky=W + E)

        self.przycisk_wyznacz.grid(row=15, column=1, columnspan=1)
        self.etykieta_dodaj.grid(row=25, column=0, columnspan=1, sticky=W + E)
        self.edytor_wsp.grid(row=26, column=0, columnspan=1, sticky=W + E)
        self.przycisk_dodaj_wsp.grid(row=26, column=1, columnspan=1)
        self.przycisk_wyczysc.grid(row=26, column=2, columnspan=3)

        self.okno_edycyjne.grid(row=0, column=4, columnspan=1, rowspan=20)

        for i in range(self.liczba_miejsc_odwiedz):
            self.lista_lok = StringVar()
            self.lista_lok = ttk.Combobox(master, state='readonly')
            self.lista_lok['values'] = self.lista_lokalizacji
            # self.lista_lok.current(1)
            self.lista_lok.grid(row=4 + i, column=1, columnspan=1)
            self.lista_lok_miejsc.append(self.lista_lok)

    def inicjalizuj_baze_danych(self):
        """
        Inicjalizuj bazę danych SQLite zawierającą tabele z danymi o lokalizacjach do odwiedzenia i czasie przejazdu
        między lokalizacjami
        :return: zwraca liczbę wszystkich możliwych lokalizacji
        """
        # utworzenie tabeli lokalizacje
        self.kursor.execute("CREATE TABLE IF NOT EXISTS lokalizacje (id_lok INTEGER PRIMARY KEY, wspolrzedne TEXT, \
                                                                                                        miasto TEXT);")
        # sprawdzenie czy tabela lokalizacje jest pusta
        self.kursor.execute("SELECT * FROM lokalizacje")
        dane = self.kursor.fetchall()
        if len(dane) == 0:
            # jeżeli jest pusta wstaw dane z pliku .csv
            with open("lokalizacje.csv", newline='') as plik_csv:
                odczyt = csv.reader(plik_csv, delimiter=';', quotechar='|')
                for wiersz in odczyt:
                    self.kursor.execute("INSERT into lokalizacje (wspolrzedne, miasto) values (?, ?)", (wiersz[0], \
                                                                                                        wiersz[1]))
        # utworzenie tabeli dla czasów przejazdów
        self.kursor.execute("CREATE TABLE IF NOT EXISTS czasy_przejazdow (id_czas INTEGER PRIMARY KEY, \
                                                                        poczatek INTEGER, koniec INTEGER, czas REAL, \
                                                                        FOREIGN KEY(poczatek) REFERENCES \
                                                                        lokalizacje(id_lok), FOREIGN KEY(koniec) \
                                                                        REFERENCES lokalizacje(id_lok));")
        self.baza_polaczenie.commit()
        # sprawdzenie czy tabela lokalizacje jest pusta
        self.kursor.execute("SELECT * FROM czasy_przejazdow")
        dane = self.kursor.fetchall()
        if len(dane) == 0:
            # jeżeli jest pusta wstaw dane z pliku .csv
            with open("czasy_przejazdow.csv", newline='') as plik_csv:
                odczyt = csv.reader(plik_csv, delimiter=';', quotechar='|')
                for wiersz in odczyt:
                    # indeksowanie od 1...
                    self.kursor.execute("INSERT into czasy_przejazdow (poczatek, koniec, czas) values (?, ?, ?)", \
                                        (int(wiersz[0]) + 1, int(wiersz[1]) + 1, float(wiersz[2])))
        self.baza_polaczenie.commit()

        # odczytanie liczby lokalizacji
        self.kursor.execute("SELECT * FROM lokalizacje")
        dane = self.kursor.fetchall()
        liczba_lok = len(dane)
        return liczba_lok

    def dodaj_dane_wsp(self, nowe_wsp, nowe_miasto):
        """
        Obsługuje dodawanie danych o nowej lokalizacji
        :param nowe_wsp: określa współrzędne geograficzne nowej lokalizacji
        :param nowe_miasto: określa nazwę mista nowej lokalizacji
        :return: False jeżeli nie powiodło się dodawanie nowej lokalizacji
                True jeśli dodanie nowej lokalizacji się powiodło
        """
        self.kursor.execute("INSERT into lokalizacje (wspolrzedne, miasto) values (?, ?)", (nowe_wsp, nowe_miasto))
        self.baza_polaczenie.commit()

        # pobierz id z tablicy lokalizacje znajdującej się w bazie danych
        self.kursor.execute("SELECT * FROM lokalizacje WHERE wspolrzedne=?", (nowe_wsp,))
        dane = self.kursor.fetchone()
        id = dane[0]

        naglowek = 'https://maps.googleapis.com/maps/api/distancematrix/json?'
        self.kursor.execute("SELECT * FROM lokalizacje WHERE wspolrzedne <> ?", (nowe_wsp,))
        tablica_dane = self.kursor.fetchall()
        for j in range(len(tablica_dane)):
            if j == id:
                self.kursor.execute("INSERT into czasy_przejazdow (poczatek, koniec, czas) values (?, ?, ?)", \
                                    (id, id, 0))

            param = 'origins={}&destinations={}&key={}'.format(dane[1], tablica_dane[j][1], self.klucz_api)
            zadanie = naglowek + param

            try:
                urllib.request.urlopen(zadanie)
            except urllib.error.HTTPError as e:
                print(e.code)
                print(e.read())
                return False
            else:
                # powodzenie
                odpowiedz = urllib.request.urlopen(zadanie).read()
                dane_json = json.loads(odpowiedz)
                if dane_json['status'] == "INVALID_REQUEST":
                    self.okno_edycyjne.insert(END, "\n\nBłąd. Niepoprawne wykonanie żadania pobrania czasu.\n\n")
                    return False
                else:
                    try:
                        czas = dane_json['rows'][0]['elements'][0]['duration']['value']
                    except:
                        return False
                    self.kursor.execute("INSERT INTO czasy_przejazdow (poczatek, koniec, czas) VALUES (?, ?, ?)", \
                                        (id, tablica_dane[j][0], czas))

            param = 'origins={}&destinations={}&key={}'.format(tablica_dane[j][1], dane[1], self.klucz_api)
            zadanie = naglowek + param

            try:
                urllib.request.urlopen(zadanie)
            except urllib.error.HTTPError as e:
                print(e.code)
                print(e.read())
                return False
            else:
                # powodzenie
                odpowiedz = urllib.request.urlopen(zadanie).read()
                dane_json = json.loads(odpowiedz)
                if dane_json['status'] == "INVALID_REQUEST":
                    self.okno_edycyjne.insert(END, "\n\nBłąd. Niepoprawne wykonanie żadania pobrania czasu.\n\n")
                    return False
                else:
                    # wprowadzono poprawne wartości
                    try:
                        czas = dane_json['rows'][0]['elements'][0]['duration']['value']
                    except:
                        return False
                    self.kursor.execute("INSERT INTO czasy_przejazdow (poczatek, koniec, czas) VALUES (?, ?, ?)", \
                                        (tablica_dane[j][0], id, czas))
        self.baza_polaczenie.commit()
        return True

    def dodaj_nowe_wsp(self):
        """
        Dodaje nowe współrzędne do bazy danych
        """
        # sprawdzenie czy współrzędne wprowadzone są poprawne
        adres = self.edytor_wsp.get()
        adres = adres.replace(" ", "+")
        naglowek = 'https://maps.googleapis.com/maps/api/geocode/json?address='
        parametry = '&key={}'.format(self.klucz_api)
        zadanie = naglowek + adres + parametry

        try:
            urllib.request.urlopen(zadanie)
        except urllib.error.HTTPError as e:
            print(e.code)
            print(e.read())
        else:
            # powodzenie
            odpowiedz = urllib.request.urlopen(zadanie).read()
            dane_json = json.loads(odpowiedz)
            if dane_json['status'] == "INVALID_REQUEST":
                self.okno_edycyjne.insert(END, "\n\nBłąd. Niepoprawna wartość współrzędnych.\n\n")
            else:
                # wprowadzono poprawne wartości współrzędnych geograficznych
                try:
                    miasto = dane_json['results'][0]['address_components'][4]['long_name']
                except:
                    self.okno_edycyjne.insert(END, "\nNie można znależć takiej lokalizacji.\n\n")
                    return
                szerokosc = dane_json['results'][0]['geometry']['location']['lat']
                dlugosc = dane_json['results'][0]['geometry']['location']['lng']
                wsp = str(szerokosc) + "," + str(dlugosc)

                res = self.dodaj_dane_wsp(wsp, miasto)
                if res:
                    self.liczba_lokalizacji += 1
                    self.lista_lokalizacji.append(miasto)
                    self.lista_wspol.append(wsp)
                    for i in range(self.liczba_miejsc_odwiedz):
                        self.lista_lok_miejsc[i]['values'] = self.lista_lokalizacji
                    self.okno_edycyjne.insert(END, "\nDodano nową lokalizację.\n\n")
                else:
                    # w przypadku niepowodzenia
                    self.kursor.execute("DELETE FROM lokalizacje WHERE wspolrzedne = ?", (wsp,))
                    self.baza_polaczenie.commit()
                    self.okno_edycyjne.insert(END, "\nNie można dodać lokalizacji.\n\n")

    def zmien_liczbe_miejsc(self):
        """\
        Zamienia liczbę miejsc do odwiedzenia
        """
        odczytana_liczba_odwiedz = int(self.wybor_liczby_lok.get())

        if odczytana_liczba_odwiedz < self.liczba_miejsc_odwiedz:
            roz = self.liczba_miejsc_odwiedz - odczytana_liczba_odwiedz

            # usunięcie elementów z listy
            for j in range(roz):
                wym = len(self.lista_lok_miejsc)
                self.lista_lok_miejsc.pop(wym - 1)

            lista_widzetow = self.master.grid_slaves()
            # usunięcie widżetów
            for i in range(roz):
                lista_widzetow[i].destroy()

            self.liczba_miejsc_odwiedz = odczytana_liczba_odwiedz

        if odczytana_liczba_odwiedz > self.liczba_miejsc_odwiedz:
            roz = odczytana_liczba_odwiedz - self.liczba_miejsc_odwiedz

            # dodanie elementów do listy
            for j in range(roz):
                self.lista_lok = StringVar()
                self.lista_lok = ttk.Combobox(self.master, state='readonly')
                self.lista_lok['values'] = self.lista_lokalizacji
                self.lista_lok.grid(row=4 + self.liczba_miejsc_odwiedz + j, column=1, columnspan=1)
                self.lista_lok_miejsc.append(self.lista_lok)

            self.liczba_miejsc_odwiedz = odczytana_liczba_odwiedz

    def wysrodkuj_okno(self, szer, wys):
        """\
        Powoduje wyśrodowanie okna aplikacji na ekranie
        :param szer: zadana wartość szerokości aplikacji
        :param wys: zadana wartość wysokości aplikacji
        :return: format zapisujący szerokość, wysokość i położenie aplikacji
        """
        # pobierz szerokość ekranu
        szer_ekr = root.winfo_screenwidth()
        wys_ekr = root.winfo_screenheight()
        # oblicz pozycję x, y
        x = (szer_ekr / 2) - (szer / 2)
        y = (wys_ekr / 2) - (wys / 2)
        root.geometry('%dx%d+%d+%d' % (szer, wys, x, y))

    def zamien_format_czasu(self, sekundy):
        """\
        Zamienia wartość czasu podaną w sekundach na format czasu - godziny : minuty
        :param sekundy: wartość czasu w sekundach
        :return: łańcuch znaków repezentujący wartość czasu w formacie: godziny : minuty
        """
        godziny = sekundy // 3600
        minuty = sekundy / 60 - godziny * 60
        return "%d h %02d min" % (godziny, minuty)

    def wczytaj_klucz_api(self, nazwa_pliku):
        """\
        Wczytuje klucz api z pliku o podanej nazwie
        :param nazwa_pliku: nazwa pliku zawierającego klucz api
        :return: łańcuch znaków definiujący klucz api
        """
        with open(nazwa_pliku) as fd:
            api_key = fd.readline()
            fd.close()
        return api_key

    def wczytaj_macierz_czasu_przejazdow(self):
        """\
        Otwiera plik o zdanej nazwie i wczytuje dane macierzy czasu przejazdu
        :param nazwa_pliku: nazwa pliku tekstowego zawierającego dane o czasach przejazdów
        :param liczba_lokalizacji: określa liczbę miejsc
        :return: zwraca macierz czasów przejazdu między lokalizacjami
        """
        mac_przejazdu = np.zeros((self.liczba_lokalizacji, self.liczba_lokalizacji))

        # wczytanie danych o nazwach miast i współrzędnych geograficznych
        self.kursor.execute("SELECT * FROM czasy_przejazdow")
        tablica_danych = self.kursor.fetchall()
        for i in range(len(tablica_danych)):
            # zmiana indeksowania - z indeksów 1... na 0...
            mac_przejazdu[tablica_danych[i][1] - 1][tablica_danych[i][2] - 1] = tablica_danych[i][3]
        return mac_przejazdu

    def wczytaj_liste_miejsc(self):
        """\
        Otwiera plik o zdanej nazwie i wczytuje dane o liście miejsc
        :param nazwa_pliku: nazwa pliku tekstowego zawierającego dane o lokalizacji
        :param liczba_lok: określa liczbę miejsc
        :return: zwraca listę współrzędnych i nazw miasto
        """
        # lista lokalizacji
        lista_lok = []

        # lista współrzędnych
        lista_wsp = []

        # wczytanie danych o nazwach miast i współrzędnych geograficznych
        self.kursor.execute("SELECT * FROM lokalizacje")
        tablica_danych = self.kursor.fetchall()
        for i in range(len(tablica_danych)):
            lista_wsp.append(tablica_danych[i][1])
            lista_lok.append(tablica_danych[i][2])
        return lista_wsp, lista_lok

    def wyznacz_poczatkowa_perm(self):
        """\
        Wyznacza poczatkową permutację dla trzech pojazdów rozdzieloną zerami
        :return: zwraca początkową permutację dla trzech pojazdów rozdzieloną zerami
        """
        perm = [0]
        for i in range(self.liczba_miejsc_odwiedz):
            perm.append(self.lista_lok_miejsc[i].current())
        perm.append(0)

        dl = len(perm)
        perm.insert(dl // 3 + 1, 0)
        perm.insert(dl * 2 // 3 + 1, 0)
        return perm

    def generuj_permutacje(self, permutacja_pop):
        """\
        Wyznacza nową permutację na podstawie danej permutacji wejściowej
        :param permutacja_pop: permutacja wejściowea
        :return: zwraca nową permutację
        """
        nowa_perm = []
        dlugosc = len(permutacja_pop)
        for i in range(dlugosc):
            nowa_perm.append(permutacja_pop[i])

        # wylosuj z permutacji dwie lokalizacje i zamień je miejscami
        poz1 = random.randint(0, dlugosc - 1)
        # sprawdzenie czy element nie jest zerowy
        while nowa_perm[poz1] == 0:
            poz1 = random.randint(0, dlugosc - 1)

        poz2 = random.randint(0, dlugosc - 1)
        while nowa_perm[poz2] == 0:
            poz2 = random.randint(0, dlugosc - 1)

        nowa_perm[poz1], nowa_perm[poz2] = nowa_perm[poz2], nowa_perm[poz1]

        return nowa_perm

    def wyznacz_czas_przejazdu(self, macierz, wektor):
        """\
        Wyznacza sumę elementów wektora
        :return:
        :param macierz: określa macierz czasu przejazdu między lokacjami
        :param wektor: określa wektor permutacji
        :return: zwraca maksymalną wartość czasu przejazdu z trzech permutacji i wektor czasów przejazdu tras
        """

        # punkt startu - Wrocław - indeks pierwszy
        wymiar = len(wektor)
        suma = 0
        tab_sum = []
        tab_czasy_dojazdu = []
        tab = []

        # wynaczenie czasów dla poszególnych części permutacji
        for i in range(1, wymiar):
            if i == 1:
                # obliczenie sumy dla pierwszego elementu
                suma += macierz[i - 1][wektor[i]]
                # dodanie nowej wartości czasu dojazdu do lokalizacji
                tab.append(macierz[i - 1][wektor[i]])
            else:
                suma += macierz[wektor[i - 1]][wektor[i]]
                # dodanie nowej wartości czasu dojazdu do lokalizacji
                tab.append(macierz[wektor[i - 1]][wektor[i]])
                if wektor[i] == 0:
                    tab_sum.append(suma)
                    suma = 0
                    tab_czasy_dojazdu.append(tab)
                    tab = []
        return max(tab_sum), tab_sum, tab_czasy_dojazdu

    def symulowane_wyzarzanie(self, macierz_czasu, T_p, T_k, wsp_lam):
        """\
        Implementacja algorytmu symulowanego wyzarzania
        :return:
        :param macierz_czasu: określa macierz czasu przejazdu między lokacjami
        :param T_p: określa temperaturę początkową
        :param T_k: określa temperaturę końcową
        :param wsp_lam: określa współczynnik iloczynowy zmiany temperatury
        :return: zwraca permutację początkową i permutację optymalną
        """
        # temperatura bieżąca
        T = T_p

        permutacja_pocz = self.wyznacz_poczatkowa_perm()

        permutacja_nowa = []

        permutacja = permutacja_pocz

        # algortym symulowanego wyżarzania

        # licznik iteracji pętli while
        licz = 0

        # wykonuj dopóki bieżąca temperatura jest większa od temperatury końcowej
        while T > T_k:
            # wygeneruj losową permutację z otoczenia Pi - N(Pi)
            permutacja_nowa = self.generuj_permutacje(permutacja)

            czas_perm, tmp1, tmp3 = self.wyznacz_czas_przejazdu(macierz_czasu, permutacja)
            czas_nowej_perm, tmp2, tmp4 = self.wyznacz_czas_przejazdu(macierz_czasu, permutacja_nowa)

            if czas_perm > czas_nowej_perm:
                permutacja = permutacja_nowa

            # różnica pomiędzy sumą elementów wektora nowej permutacji a sumą elementów wektora poprzedniej permutacji
            roznica = czas_nowej_perm - czas_perm

            if roznica <= 0:
                permutacja = permutacja_nowa
            else:
                p = exp(-roznica / T)
                z = np.random.uniform(0, 1)
                if z < p:
                    permutacja = permutacja_nowa

            # wyznaczenie kolejnej wartości temperatury
            T = wsp_lam * T

            licz += 1

        return permutacja_pocz, permutacja

    def wyczysc(self):
        """\
        Czyści okno edycyjne
        """
        self.okno_edycyjne.delete(1.0, END)

    def uruchom(self):
        """\
        Uruchamia implementację algorytmu symulowanego wyżarzania
        """
        # paramety konfiguracyjne dla algorytmu symulowanego wyżarzania
        # temperatura początkowa
        T_poczatkowa = 1000

        # temperatura końcowa
        T_koncowa = 0.1

        # współczynnik zmiany temperatury
        wsp_lambda = 0.995

        # wczytanie macierzy zawierącej czasu przejazdów między lokalizacjami
        macierz_c = self.wczytaj_macierz_czasu_przejazdow()

        # wywołanie metody implementującej algorytm symulowanego wyżarzania dla znalezienia optymalnej permutacji
        perm_pocz, perm_opt = self.symulowane_wyzarzanie(macierz_c, T_poczatkowa, T_koncowa, wsp_lambda)

        wym = len(perm_opt)
        lista_pocz_przejazdu = []
        lista_optymal_przejazdu = []

        for i in range(wym):
            lista_pocz_przejazdu.append(self.lista_lokalizacji[perm_pocz[i]])
            lista_optymal_przejazdu.append(self.lista_lokalizacji[perm_opt[i]])

        czas_prz_pocz, czasy_przejazdu_pocz, tab_czasy_dojazdu_pocz = self.wyznacz_czas_przejazdu(macierz_c, perm_pocz)
        czas_prz_opt, czasy_przejazdu_opt, tab_czasy_dojazdu_opt = self.wyznacz_czas_przejazdu(macierz_c, perm_opt)

        dl_perm = len(perm_pocz)
        indeks = 1
        znal = 0
        permutacja_pierw_pocz = [self.lista_wspol[0]]
        permutacja_drug_pocz = [self.lista_wspol[0]]
        permutacja_trz_pocz = [self.lista_wspol[0]]

        trasa_pierw_pocz = [self.lista_lokalizacji[0]]
        trasa_drug_pocz = [self.lista_lokalizacji[0]]
        trasa_trz_pocz = [self.lista_lokalizacji[0]]

        # wektory czasów dojazdu dla początkowych tras
        wekt_dojazd_pierw_pocz = tab_czasy_dojazdu_pocz[0]
        wekt_dojazd_drug_pocz = tab_czasy_dojazdu_pocz[1]
        wekt_dojazd_trz_pocz = tab_czasy_dojazdu_pocz[2]

        while znal != 1 and indeks < dl_perm:
            if perm_pocz[indeks] != 0 and znal != 1:
                permutacja_pierw_pocz.append(self.lista_wspol[perm_pocz[indeks]])
                trasa_pierw_pocz.append(self.lista_lokalizacji[perm_pocz[indeks]])
                indeks += 1
            else:
                znal = 1
        permutacja_pierw_pocz.append(self.lista_wspol[0])
        trasa_pierw_pocz.append(self.lista_lokalizacji[0])

        indeks += 1
        znal = 0
        while znal != 1 and indeks < dl_perm:
            if perm_pocz[indeks] != 0 and znal != 1:
                permutacja_drug_pocz.append(self.lista_wspol[perm_pocz[indeks]])
                trasa_drug_pocz.append(self.lista_lokalizacji[perm_pocz[indeks]])
                indeks += 1
            else:
                znal = 1
        permutacja_drug_pocz.append(self.lista_wspol[0])
        trasa_drug_pocz.append(self.lista_lokalizacji[0])

        indeks += 1
        znal = 0
        while znal != 1 and indeks < dl_perm:
            if perm_pocz[indeks] != 0 and znal != 1:
                permutacja_trz_pocz.append(self.lista_wspol[perm_pocz[indeks]])
                trasa_trz_pocz.append(self.lista_lokalizacji[perm_pocz[indeks]])
                indeks += 1
            else:
                znal = 1
        permutacja_trz_pocz.append(self.lista_wspol[0])
        trasa_trz_pocz.append(self.lista_lokalizacji[0])

        dl_perm = len(perm_opt)
        indeks = 1
        znal = 0
        permutacja_pierw = [self.lista_wspol[0]]
        permutacja_drug = [self.lista_wspol[0]]
        permutacja_trz = [self.lista_wspol[0]]

        trasa_pierw = [self.lista_lokalizacji[0]]
        trasa_drug = [self.lista_lokalizacji[0]]
        trasa_trz = [self.lista_lokalizacji[0]]

        # wektory czasów dojazdu dla wyznaczonych tras
        wekt_dojazd_pierw_opt = tab_czasy_dojazdu_opt[0]
        wekt_dojazd_drug_opt = tab_czasy_dojazdu_opt[1]
        wekt_dojazd_trz_opt = tab_czasy_dojazdu_opt[2]

        while znal != 1 and indeks < dl_perm:
            if perm_opt[indeks] != 0 and znal != 1:
                permutacja_pierw.append(self.lista_wspol[perm_opt[indeks]])
                trasa_pierw.append(self.lista_lokalizacji[perm_opt[indeks]])
                indeks += 1
            else:
                znal = 1
        permutacja_pierw.append(self.lista_wspol[0])
        trasa_pierw.append(self.lista_lokalizacji[0])

        indeks += 1
        znal = 0
        while znal != 1 and indeks < dl_perm:
            if perm_opt[indeks] != 0 and znal != 1:
                permutacja_drug.append(self.lista_wspol[perm_opt[indeks]])
                trasa_drug.append(self.lista_lokalizacji[perm_opt[indeks]])
                indeks += 1
            else:
                znal = 1
        permutacja_drug.append(self.lista_wspol[0])
        trasa_drug.append(self.lista_lokalizacji[0])

        indeks += 1
        znal = 0
        while znal != 1 and indeks < dl_perm:
            if perm_opt[indeks] != 0 and znal != 1:
                permutacja_trz.append(self.lista_wspol[perm_opt[indeks]])
                trasa_trz.append(self.lista_lokalizacji[perm_opt[indeks]])
                indeks += 1
            else:
                znal = 1
        permutacja_trz.append(self.lista_wspol[0])
        trasa_trz.append(self.lista_lokalizacji[0])

        # wyświetlenie początkowych permutacji dla pojazdów
        # trasa dla pierwszego pojazdu
        self.okno_edycyjne.insert(END, "\nPoczątkowa trasa dla pierwszego pojazdu \n")
        for j in range(len(permutacja_pierw_pocz)):
            self.okno_edycyjne.insert(END, permutacja_pierw_pocz[j])
            self.okno_edycyjne.insert(END, "\t\t")
            self.okno_edycyjne.insert(END, trasa_pierw_pocz[j])
            if j != 0:
                self.okno_edycyjne.insert(END, "\t\tczas dojazdu: ")
                self.okno_edycyjne.insert(END, self.zamien_format_czasu(wekt_dojazd_pierw_pocz[j-1]))
            self.okno_edycyjne.insert(END, "\n")
        # trasa dla drugiego pojazdu
        self.okno_edycyjne.insert(END, "\nPoczątkowa trasa dla drugiego pojazdu \n")
        for j in range(len(permutacja_drug_pocz)):
            self.okno_edycyjne.insert(END, permutacja_drug_pocz[j])
            self.okno_edycyjne.insert(END, "\t\t")
            self.okno_edycyjne.insert(END, trasa_drug_pocz[j])
            if j != 0:
                self.okno_edycyjne.insert(END, "\t\tczas dojazdu: ")
                self.okno_edycyjne.insert(END, self.zamien_format_czasu(wekt_dojazd_drug_pocz[j - 1]))
            self.okno_edycyjne.insert(END, "\n")
        # trasa dla trzeciego pojazdu
        self.okno_edycyjne.insert(END, "\nPoczątkowa trasa dla trzeciego pojazdu \n")
        for j in range(len(permutacja_trz_pocz)):
            self.okno_edycyjne.insert(END, permutacja_trz_pocz[j])
            self.okno_edycyjne.insert(END, "\t\t")
            self.okno_edycyjne.insert(END, trasa_trz_pocz[j])
            if j != 0:
                self.okno_edycyjne.insert(END, "\t\tczas dojazdu: ")
                self.okno_edycyjne.insert(END, self.zamien_format_czasu(wekt_dojazd_trz_pocz[j - 1]))
            self.okno_edycyjne.insert(END, "\n")

        # wyświelenie wartości czasów przejazdu poszególnych tras przy początkowej permutacji
        self.okno_edycyjne.insert(END, "\nCzas przejazdu dla pierwszego pojazdu\n")
        self.okno_edycyjne.insert(END, self.zamien_format_czasu(czasy_przejazdu_pocz[0]))
        self.okno_edycyjne.insert(END, "\n\nCzas przejazdu dla drugiego pojazdu\n")
        self.okno_edycyjne.insert(END, self.zamien_format_czasu(czasy_przejazdu_pocz[1]))
        self.okno_edycyjne.insert(END, "\n\nCzas przejazdu dla trzeciego pojazdu\n")
        self.okno_edycyjne.insert(END, self.zamien_format_czasu(czasy_przejazdu_pocz[2]))
        self.okno_edycyjne.insert(END, "\n\n")

        # wyświetlenie permutacji dla pojazdów wyznaczonych algorytmem symulowanego wyżarzania
        # trasa dla pierwszego pojazdu
        self.okno_edycyjne.insert(END, "\nWyznaczona trasa dla pierwszego pojazdu \n")
        for j in range(len(permutacja_pierw)):
            self.okno_edycyjne.insert(END, permutacja_pierw[j])
            self.okno_edycyjne.insert(END, "\t\t")
            self.okno_edycyjne.insert(END, trasa_pierw[j])
            if j != 0:
                self.okno_edycyjne.insert(END, "\t\tczas dojazdu: ")
                self.okno_edycyjne.insert(END, self.zamien_format_czasu(wekt_dojazd_pierw_opt[j - 1]))
            self.okno_edycyjne.insert(END, "\n")
        # trasa dla drugiego pojazdu
        self.okno_edycyjne.insert(END, "\nWyznaczona trasa dla drugiego pojazdu \n")
        for j in range(len(permutacja_drug)):
            self.okno_edycyjne.insert(END, permutacja_drug[j])
            self.okno_edycyjne.insert(END, "\t\t")
            self.okno_edycyjne.insert(END, trasa_drug[j])
            if j != 0:
                self.okno_edycyjne.insert(END, "\t\tczas dojazdu: ")
                self.okno_edycyjne.insert(END, self.zamien_format_czasu(wekt_dojazd_drug_opt[j - 1]))
            self.okno_edycyjne.insert(END, "\n")
        # trasa dla trzeciego pojazdu
        self.okno_edycyjne.insert(END, "\nWyznaczona trasa dla trzeciego pojazdu \n")
        for j in range(len(permutacja_trz)):
            self.okno_edycyjne.insert(END, permutacja_trz[j])
            self.okno_edycyjne.insert(END, "\t\t")
            self.okno_edycyjne.insert(END, trasa_trz[j])
            if j != 0:
                self.okno_edycyjne.insert(END, "\t\tczas dojazdu: ")
                self.okno_edycyjne.insert(END, self.zamien_format_czasu(wekt_dojazd_trz_opt[j - 1]))
            self.okno_edycyjne.insert(END, "\n")
        # wyświelenie wartości czasów przejazdu poszególnych tras dla permutacji optymalnej
        self.okno_edycyjne.insert(END, "\nCzas przejazdu dla pierwszego pojazdu\n")
        self.okno_edycyjne.insert(END, self.zamien_format_czasu(czasy_przejazdu_opt[0]))
        self.okno_edycyjne.insert(END, "\n\nCzas przejazdu dla drugiego pojazdu\n")
        self.okno_edycyjne.insert(END, self.zamien_format_czasu(czasy_przejazdu_opt[1]))
        self.okno_edycyjne.insert(END, "\n\nCzas przejazdu dla trzeciego pojazdu\n")
        self.okno_edycyjne.insert(END, self.zamien_format_czasu(czasy_przejazdu_opt[2]))
        self.okno_edycyjne.insert(END, "\n\n")

        # wykreślenie map tras dla trzech pojazdów
        adres_mapy = "https://www.google.com/maps/dir/?api=1&origin="

        # wyrysowanie trasy dla pierwszego pojazdu
        adres_mapy += permutacja_pierw[0]
        adres_mapy += "&destination="
        adres_mapy += permutacja_pierw[len(permutacja_pierw) - 1]
        adres_mapy += "&waypoints="
        for k in range(1, len(permutacja_pierw) - 1):
            adres_mapy += "%7C"
            adres_mapy += permutacja_pierw[k]

        adres_mapy += "&travelmode=driving&key="
        adres_mapy += self.klucz_api
        webbrowser.open(adres_mapy)

        # wyrysowanie trasy dla drugiego pojazdu
        adres_mapy = "https://www.google.com/maps/dir/?api=1&origin="
        adres_mapy += permutacja_drug[0]
        adres_mapy += "&destination="
        adres_mapy += permutacja_drug[len(permutacja_drug) - 1]
        adres_mapy += "&waypoints="
        for k in range(1, len(permutacja_drug) - 1):
            adres_mapy += "%7C"
            adres_mapy += permutacja_drug[k]

        adres_mapy += "&travelmode=driving&key="
        adres_mapy += self.klucz_api
        webbrowser.open(adres_mapy)

        # wyrysowanie trasy dla trzeciego pojazdu
        adres_mapy = "https://www.google.com/maps/dir/?api=1&origin="
        adres_mapy += permutacja_trz[0]
        adres_mapy += "&destination="
        adres_mapy += permutacja_trz[len(permutacja_trz) - 1]
        adres_mapy += "&waypoints="
        for k in range(1, len(permutacja_trz) - 1):
            adres_mapy += "%7C"
            adres_mapy += permutacja_trz[k]

        adres_mapy += "&travelmode=driving&key="
        adres_mapy += self.klucz_api
        webbrowser.open(adres_mapy)


root = Tk()
interfejs = Aplikacja(root)

interfejs.wysrodkuj_okno(666, 320)
Tk.minsize(root, width=760, height=400)
root.mainloop()
