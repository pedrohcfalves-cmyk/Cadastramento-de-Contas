import re
from textwrap import fill

from playwright.sync_api import Page, sync_playwright

URL_manter_credor = "http://sigef.sefin.ro.gov.br/SIGEF2026/ADM/ADMManterCredorGeral.aspx?CdTransacao=1028"

URL_incluir_domicilio = "http://sigef.sefin.ro.gov.br/SIGEF2026/FIN/FINIncluirDomicilioBancarioCredor.aspx?CdTransacao=351"

with sync_playwright() as p:

    try:
        browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    except Exception:
        raise Exception(
            "Chrome em modo de depuração não encontrado.\n"
            "Abra o Chrome com:\n"
            "\"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe\" "
            "--remote-debugging-port=9222"
        )

    context = browser.contexts[0]

    page = None

    # Procura uma aba do SIGEF já aberta
    for aba in context.pages:
        print("Aba:", aba.url)

        if "sigef.sefin.ro.gov.br" in aba.url.lower():
            page = aba
            print("SIGEF encontrado.")
            break

    # Se não existir uma aba do SIGEF, cria uma
    if page is None:
        page = context.new_page()
        page.goto(URL_manter_credor)
    else:
        page.bring_to_front()

        if "ADMManterCredorGeral" not in page.url:
            page.goto(URL_manter_credor)

    page.wait_for_load_state("networkidle")

    # ========= SUA AUTOMAÇÃO =========

    page.locator("#cmbTipoCredor").select_option("10")

    with page.expect_popup() as popup_info:
        page.locator("#btnManutencao_BtnListar").click()

    nova_page = popup_info.value
    nova_page.wait_for_load_state()

    nova_page.locator("#txtCPF").fill("00000000000") #Colocar o CPF
    nova_page.locator("#btnConfirmar").click()

    cadastro = nova_page.locator("#dtgCredor td[onclick]")

    if cadastro.count() == 0:

        # ====================================
        # CAMINHO 1 - SEM CREDOR - CADASTRAR
        # ====================================

        nova_page.close()
        page.bring_to_front()
        page.locator("#txtCPF").fill("00000000000") #Colocar o CPF
        page.locator("#btnReceitaFederal").click()
        page.locator("#txtNmCredor").fill("NOME DO CREDOR") #Colocar o nome do credor
        page.locator("#btnManutencao_BtnIncluir").click()

        #Cadastrar Domicílio Bancário

        page.goto(URL_incluir_domicilio)
        page.wait_for_load_state("networkidle")
    
        with page.expect_popup() as popup_info:
            page.locator("#txtCdCredor_BtnPesquisa").click()
            
        nova_page = popup_info.value
        nova_page.wait_for_load_state()
    
        nova_page.locator("#btnCPF").click()
        nova_page.locator("#txtNuCpf").fill("00000000000") #Colocar o CPF
        nova_page.locator("#btnConfirmar").click()
    
        tabelacpf = nova_page.locator("#dtgCredor td[onclick]")
        tabelacpf.first.click()
    
        page.bring_to_front()
        page.locator("#txtBanco_SIGEFPesquisa").press_sequentially("001") 
        page.locator("#txtAgBancaria_SIGEFPesquisa").press_sequentially("1234") 
        page.locator("#txtContaBancaria").press_sequentially("123456") 
        page.locator("#txtNmContaBancaria").fill("NOME DO CREDOR") #Nome da conta bancária
        page.locator("#btnConfirmar").click()

        ...

    else:

        # ====================================
        # CAMINHO 2 - COM CREDOR Cadastrado - INCLUIR DOMICÍLIO BANCÁRIO
        # ====================================

        cadastro.first.click()
        page.bring_to_front()
        page.goto(URL_incluir_domicilio)
        page.wait_for_load_state("networkidle")

        with page.expect_popup() as popup_info:
            page.locator("#txtCdCredor_BtnPesquisa").click()
        
        nova_page = popup_info.value
        nova_page.wait_for_load_state()

        nova_page.locator("#btnCPF").click()
        nova_page.locator("#txtNuCpf").fill("00000000000") #Colocar o CPF
        nova_page.locator("#btnConfirmar").click()

        tabelacpf = nova_page.locator("#dtgCredor td[onclick]")
        tabelacpf.first.click()

        page.bring_to_front()
        page.locator("#txtBanco_SIGEFPesquisa").press_sequentially("001") 
        page.locator("#txtAgBancaria_SIGEFPesquisa").press_sequentially("1234") 
        page.locator("#txtContaBancaria").press_sequentially("123456") 
        page.locator("#txtNmContaBancaria").fill("NOME DO CREDOR") #Nome da conta bancária
        page.locator("#btnConfirmar").click()

        # todo o fluxo 2 aqui
        ...

