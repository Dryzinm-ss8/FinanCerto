import calendar
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox

import customtkinter as ctk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from database.database import (
    adicionar_movimentacao,
    listar_movimentacoes,
    obter_resumo,
    obter_resumo_mensal,
    obter_despesas_por_categoria,
    obter_historico_mensal,
    excluir_movimentacoes,
)

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class FinanCerto(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("FinanCerto | Controle Financeiro")
        self.geometry("1200x800")
        self.minsize(1000, 680)

        agora = datetime.now()
        self.ano_selecionado = agora.year
        self.mes_selecionado = agora.month
        self._figuras = []

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.criar_menu()
        self.criar_dashboard()
        self.atualizar_dashboard()

    def criar_menu(self):
        self.menu = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.menu.grid(row=0, column=0, sticky="nsew")
        self.menu.grid_propagate(False)

        ctk.CTkLabel(
            self.menu, text="💰 FinanCerto",
            font=("Arial", 25, "bold")
        ).pack(pady=(30, 40))

        botoes = [
            ("🏠  Dashboard", self.abrir_dashboard),
            ("💸  Movimentações", self.abrir_movimentacoes),
            ("➕  Nova movimentação", self.abrir_formulario),
        ]
        for texto, comando in botoes:
            ctk.CTkButton(
                self.menu, text=texto, height=42, anchor="w",
                fg_color="transparent", hover_color="#263449",
                command=comando
            ).pack(fill="x", padx=12, pady=5)

        ctk.CTkLabel(
            self.menu, text="Seu dinheiro sob controle.",
            font=("Arial", 11), text_color="gray"
        ).pack(side="bottom", pady=20)

    def criar_dashboard(self):
        self.conteudo = ctk.CTkScrollableFrame(
            self, corner_radius=0, fg_color="transparent"
        )
        self.conteudo.grid(
            row=0, column=1, sticky="nsew", padx=22, pady=18
        )
        self.conteudo.grid_columnconfigure((0, 1, 2), weight=1)

        self.titulo = ctk.CTkLabel(
            self.conteudo, text="Dashboard financeiro",
            font=("Arial", 28, "bold")
        )
        self.titulo.grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 4)
        )
        self.subtitulo = ctk.CTkLabel(
            self.conteudo,
            text="Resumo mensal, evolução e distribuição das despesas.",
            text_color="gray"
        )
        self.subtitulo.grid(
            row=1, column=0, columnspan=3, sticky="w", pady=(0, 14)
        )

        seletor = ctk.CTkFrame(self.conteudo, fg_color="transparent")
        seletor.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(0, 12))
        ctk.CTkLabel(seletor, text="Mês de referência:").pack(side="left", padx=(0, 8))

        meses = [calendar.month_name[i] for i in range(1, 13)]
        self.escolha_mes = ctk.CTkOptionMenu(
            seletor, values=meses, width=145, command=self.mudar_mes
        )
        self.escolha_mes.set(calendar.month_name[self.mes_selecionado])
        self.escolha_mes.pack(side="left", padx=(0, 8))

        anos = [str(ano) for ano in range(datetime.now().year - 10, datetime.now().year + 2)]
        self.escolha_ano = ctk.CTkOptionMenu(
            seletor, values=anos, width=100, command=self.mudar_ano
        )
        self.escolha_ano.set(str(self.ano_selecionado))
        self.escolha_ano.pack(side="left")

        self.cartoes = ctk.CTkFrame(self.conteudo, fg_color="transparent")
        self.cartoes.grid(row=3, column=0, columnspan=3, sticky="ew")
        self.cartoes.grid_columnconfigure((0, 1, 2), weight=1)

        self.lbl_saldo = self.criar_cartao(self.cartoes, "Saldo do mês", 0)
        self.lbl_receitas = self.criar_cartao(self.cartoes, "Receitas do mês", 1)
        self.lbl_despesas = self.criar_cartao(self.cartoes, "Despesas do mês", 2)

        self.paineis_graficos = ctk.CTkFrame(self.conteudo, fg_color="transparent")
        self.paineis_graficos.grid(
            row=4, column=0, columnspan=3, sticky="ew", pady=(18, 4)
        )
        self.paineis_graficos.grid_columnconfigure((0, 1), weight=1)

        self.frame_historico = ctk.CTkFrame(self.paineis_graficos, corner_radius=12)
        self.frame_historico.grid(row=0, column=0, sticky="nsew", padx=(0, 7))
        self.frame_categorias = ctk.CTkFrame(self.paineis_graficos, corner_radius=12)
        self.frame_categorias.grid(row=0, column=1, sticky="nsew", padx=(7, 0))

        self.painel = ctk.CTkFrame(self.conteudo, corner_radius=12)
        self.painel.grid(
            row=5, column=0, columnspan=3, sticky="nsew", pady=(14, 0)
        )
        ctk.CTkLabel(
            self.painel, text="Movimentações recentes",
            font=("Arial", 19, "bold")
        ).pack(anchor="w", padx=15, pady=(15, 5))

        estilo = ttk.Style()
        try:
            estilo.theme_use("clam")
            estilo.configure(
                "Treeview", background="#242424", foreground="white",
                fieldbackground="#242424", rowheight=28
            )
            estilo.configure(
                "Treeview.Heading", background="#343638",
                foreground="white", font=("Arial", 10, "bold")
            )
            estilo.map("Treeview", background=[("selected", "#1f6aa5")])
        except tk.TclError:
            pass

        self.tabela = ttk.Treeview(
            self.painel,
            columns=("descricao", "tipo", "categoria", "valor", "data"),
            show="headings", height=8, selectmode="extended"
        )
        colunas = {
            "descricao": ("Descrição", 220),
            "tipo": ("Tipo", 90),
            "categoria": ("Categoria", 130),
            "valor": ("Valor", 120),
            "data": ("Data", 110),
        }
        for coluna, (titulo, largura) in colunas.items():
            self.tabela.heading(coluna, text=titulo)
            self.tabela.column(coluna, width=largura, anchor="center")

        self.tabela.pack(fill="both", expand=True, padx=15, pady=10)

        botoes = ctk.CTkFrame(self.conteudo, fg_color="transparent")
        botoes.grid(row=6, column=0, columnspan=3, sticky="ew", pady=(12, 18))
        ctk.CTkButton(
            botoes, text="+ Nova movimentação",
            command=self.abrir_formulario
        ).pack(side="left", padx=(0, 10))
        ctk.CTkButton(
            botoes, text="Excluir selecionada(s)",
            fg_color="#A93226", hover_color="#922B21",
            command=self.excluir_movimentacao
        ).pack(side="left")

    def criar_cartao(self, pai, titulo, coluna):
        cartao = ctk.CTkFrame(pai, corner_radius=12)
        cartao.grid(row=0, column=coluna, sticky="ew", padx=5)
        ctk.CTkLabel(
            cartao, text=titulo, text_color="gray",
            font=("Arial", 13)
        ).pack(anchor="w", padx=15, pady=(16, 5))
        valor = ctk.CTkLabel(
            cartao, text="R$ 0,00", font=("Arial", 22, "bold")
        )
        valor.pack(anchor="w", padx=15, pady=(0, 16))
        return valor

    @staticmethod
    def formatar_moeda(valor):
        texto = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"R$ {texto}"

    def mudar_mes(self, valor):
        self.mes_selecionado = list(calendar.month_name).index(valor)
        self.atualizar_dashboard()

    def mudar_ano(self, valor):
        self.ano_selecionado = int(valor)
        self.atualizar_dashboard()

    def limpar_graficos(self):
        for widget in self.frame_historico.winfo_children():
            widget.destroy()
        for widget in self.frame_categorias.winfo_children():
            widget.destroy()
        self._figuras.clear()

    def desenhar_graficos(self):
        self.limpar_graficos()

        # Histórico de receitas e despesas nos últimos seis meses.
        ctk.CTkLabel(
            self.frame_historico, text="Receitas x despesas (6 meses)",
            font=("Arial", 15, "bold")
        ).pack(anchor="w", padx=12, pady=(12, 0))

        historico = obter_historico_mensal()
        figura1 = Figure(figsize=(5.2, 3.0), dpi=90)
        eixo = figura1.add_subplot(111)
        figura1.patch.set_facecolor("#2b2b2b")
        eixo.set_facecolor("#2b2b2b")
        if historico:
            periodos = [linha[0] for linha in historico]
            receitas = [linha[1] or 0 for linha in historico]
            despesas = [linha[2] or 0 for linha in historico]
            posicoes = list(range(len(periodos)))
            largura = 0.36
            eixo.bar([p - largura / 2 for p in posicoes], receitas, largura, label="Receitas")
            eixo.bar([p + largura / 2 for p in posicoes], despesas, largura, label="Despesas")
            eixo.set_xticks(posicoes)
            eixo.set_xticklabels(
                [datetime.strptime(p, "%Y-%m").strftime("%m/%y") for p in periodos],
                color="white"
            )
            eixo.legend(facecolor="#2b2b2b", labelcolor="white", fontsize=8)
        else:
            eixo.text(0.5, 0.5, "Sem dados nos últimos meses", ha="center", va="center", color="white")
        eixo.tick_params(axis="y", colors="white", labelsize=8)
        eixo.grid(axis="y", alpha=0.2)
        for borda in eixo.spines.values():
            borda.set_color("#555555")
        figura1.tight_layout()
        canvas1 = FigureCanvasTkAgg(figura1, master=self.frame_historico)
        canvas1.draw()
        canvas1.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=5)
        self._figuras.append((figura1, canvas1))

        # Distribuição das despesas por categoria no mês selecionado.
        ctk.CTkLabel(
            self.frame_categorias, text="Despesas por categoria",
            font=("Arial", 15, "bold")
        ).pack(anchor="w", padx=12, pady=(12, 0))

        categorias = obter_despesas_por_categoria(
            self.ano_selecionado, self.mes_selecionado
        )
        figura2 = Figure(figsize=(5.2, 3.0), dpi=90)
        eixo2 = figura2.add_subplot(111)
        figura2.patch.set_facecolor("#2b2b2b")
        eixo2.set_facecolor("#2b2b2b")
        if categorias:
            nomes = [item[0] for item in categorias]
            valores = [item[1] for item in categorias]
            eixo2.pie(
                valores, labels=nomes, autopct="%1.0f%%",
                startangle=90, textprops={"color": "white", "fontsize": 8}
            )
        else:
            eixo2.text(0.5, 0.5, "Sem despesas neste mês", ha="center", va="center", color="white")
            eixo2.set_xticks([])
            eixo2.set_yticks([])
        figura2.tight_layout()
        canvas2 = FigureCanvasTkAgg(figura2, master=self.frame_categorias)
        canvas2.draw()
        canvas2.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=5)
        self._figuras.append((figura2, canvas2))

    def atualizar_dashboard(self):
        resumo = obter_resumo_mensal(self.ano_selecionado, self.mes_selecionado)
        self.lbl_saldo.configure(text=self.formatar_moeda(resumo["saldo"]))
        self.lbl_receitas.configure(text=self.formatar_moeda(resumo["receitas"]))
        self.lbl_despesas.configure(text=self.formatar_moeda(resumo["despesas"]))

        for item in self.tabela.get_children():
            self.tabela.delete(item)
        for registro in listar_movimentacoes()[:15]:
            identificador, descricao, valor, tipo, categoria, data = registro
            data_exibida = data
            try:
                data_exibida = datetime.strptime(data, "%Y-%m-%d").strftime("%d/%m/%Y")
            except ValueError:
                pass
            self.tabela.insert(
                "", "end", iid=str(identificador),
                values=(descricao, tipo, categoria, self.formatar_moeda(valor), data_exibida)
            )
        self.desenhar_graficos()

    def abrir_formulario(self):
        janela = ctk.CTkToplevel(self)
        janela.title("Nova movimentação")
        janela.geometry("430x570")
        janela.resizable(False, False)
        janela.transient(self)
        janela.grab_set()

        ctk.CTkLabel(
            janela, text="Nova movimentação", font=("Arial", 24, "bold")
        ).pack(pady=(25, 20))

        ctk.CTkLabel(janela, text="Descrição").pack(anchor="w", padx=35)
        entrada_descricao = ctk.CTkEntry(
            janela, placeholder_text="Ex.: Salário, mercado..."
        )
        entrada_descricao.pack(fill="x", padx=35, pady=(5, 12))

        ctk.CTkLabel(janela, text="Valor (R$)").pack(anchor="w", padx=35)
        entrada_valor = ctk.CTkEntry(janela, placeholder_text="Ex.: 150,50")
        entrada_valor.pack(fill="x", padx=35, pady=(5, 12))

        ctk.CTkLabel(janela, text="Tipo").pack(anchor="w", padx=35)
        escolha_tipo = ctk.CTkOptionMenu(janela, values=["Receita", "Despesa"])
        escolha_tipo.pack(fill="x", padx=35, pady=(5, 12))

        categorias = [
            "Salário", "Alimentação", "Transporte", "Moradia", "Lazer",
            "Saúde", "Educação", "Assinaturas", "Investimentos", "Outros"
        ]
        ctk.CTkLabel(janela, text="Categoria").pack(anchor="w", padx=35)
        escolha_categoria = ctk.CTkOptionMenu(janela, values=categorias)
        escolha_categoria.pack(fill="x", padx=35, pady=(5, 12))

        ctk.CTkLabel(janela, text="Data (DD/MM/AAAA)").pack(anchor="w", padx=35)
        entrada_data = ctk.CTkEntry(
            janela, placeholder_text="DD/MM/AAAA"
        )
        entrada_data.insert(0, datetime.now().strftime("%d/%m/%Y"))
        entrada_data.pack(fill="x", padx=35, pady=(5, 20))

        def salvar():
            descricao = entrada_descricao.get().strip()
            valor_texto = entrada_valor.get().strip()
            tipo = escolha_tipo.get()
            categoria = escolha_categoria.get()
            data_texto = entrada_data.get().strip()

            if not descricao:
                messagebox.showwarning("Atenção", "Informe a descrição.", parent=janela)
                return
            try:
                valor_normalizado = valor_texto.replace("R$", "").replace(" ", "")
                if "," in valor_normalizado:
                    valor_normalizado = valor_normalizado.replace(".", "").replace(",", ".")
                valor = float(valor_normalizado)
                if valor <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror(
                    "Valor inválido", "Digite um valor maior que zero. Ex.: 150,50",
                    parent=janela
                )
                return
            try:
                data = datetime.strptime(data_texto, "%d/%m/%Y").strftime("%Y-%m-%d")
            except ValueError:
                messagebox.showerror(
                    "Data inválida", "Digite uma data válida no formato DD/MM/AAAA.",
                    parent=janela
                )
                return

            try:
                adicionar_movimentacao(descricao, valor, tipo, categoria, data)
                self.atualizar_dashboard()
                # Mantém o mês de referência alinhado com a movimentação salva.
                data_obj = datetime.strptime(data, "%Y-%m-%d")
                self.mes_selecionado, self.ano_selecionado = data_obj.month, data_obj.year
                self.escolha_mes.set(calendar.month_name[self.mes_selecionado])
                self.escolha_ano.set(str(self.ano_selecionado))
                self.atualizar_dashboard()
                messagebox.showinfo("Sucesso", "Movimentação salva com sucesso!", parent=janela)
                janela.destroy()
            except Exception as erro:
                messagebox.showerror(
                    "Erro", f"Não foi possível salvar a movimentação.\n{erro}",
                    parent=janela
                )

        ctk.CTkButton(
            janela, text="Salvar movimentação", height=42, command=salvar
        ).pack(fill="x", padx=35, pady=(0, 20))

    def excluir_movimentacao(self):
        selecionados = self.tabela.selection()
        if not selecionados:
            messagebox.showwarning(
                "Atenção", "Selecione uma movimentação para excluir.", parent=self
            )
            return
        confirmar = messagebox.askyesno(
            "Confirmar exclusão",
            "Deseja realmente excluir a(s) movimentação(ões) selecionada(s)?",
            parent=self
        )
        if not confirmar:
            return
        try:
            excluir_movimentacoes([int(item) for item in selecionados])
            self.atualizar_dashboard()
            messagebox.showinfo("Sucesso", "Movimentação(ões) excluída(s).", parent=self)
        except Exception as erro:
            messagebox.showerror("Erro", f"Não foi possível excluir.\n{erro}", parent=self)

    def abrir_dashboard(self):
        self.titulo.configure(text="Dashboard financeiro")
        self.subtitulo.configure(
            text="Resumo mensal, evolução e distribuição das despesas."
        )
        self.atualizar_dashboard()

    def abrir_movimentacoes(self):
        self.titulo.configure(text="Todas as movimentações")
        self.subtitulo.configure(
            text="As movimentações mais recentes aparecem na tabela abaixo."
        )
        self.atualizar_dashboard()


if __name__ == "__main__":
    app = FinanCerto()
    app.mainloop()
