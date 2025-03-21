import dash_chart_editor as dce
import dash_mantine_components as dmc
import plotly.express as px
import plotly.graph_objs as go
from dash import ALL, Dash, Input, Output, Patch, State, ctx, dcc, no_update


class ChartEditor:
    def __init__(  # noqa: PLR0913, PLR0917
        self,
        app,
        instance_id='main',  # Novo parâmetro para identificar a instância
        data_source=None,
        container_id='pattern-match-container',
        modal_size='85%',
        default_figures=None,
        figure_titles=None,  # Novo parâmetro para títulos específicos
        default_title='Figure',  # Renomeado de figure_title para default_title
        card_size=400,
        initial_cards=0,
        update_interval_id=None,
        data_update_function=None,
    ):
        """
        Inicializa o editor de gráficos

        Args:
            app: Instância do Dash app
            instance_id: ID único para esta instância doeditor(evita conflitos)
            data_source: Dicionário com os dados para o editor
            container_id: ID do container onde os cards serão renderizados
            modal_size: Tamanho do modal
            default_figures: Lista de figuras padrão para os cards.
            Se None ou lista menor que necessário,
            usa go.Figure() para completar
            figure_titles: Lista de títulos específicos para cada figura
            default_title: Título padrão quando não há título específico
            card_size: Tamanho dos cards em pixels
            initial_cards: Número de cards para criar inicialmente
            update_interval_id: ID do componente de
            intervalo para atualização periódica
            data_update_function: Função que retorna
            dados atualizados quando chamada
        """
        self.app = app
        self.instance_id = instance_id
        self.container_id = f'{instance_id}-{container_id}'
        self.card_size = card_size

        self.data_source = (
            data_source.to_dict('list')
            if data_source is not None
            else px.data.iris().to_dict('list')
        )
        self.df1 = self.data_source
        # Converter entrada única em lista se necessário
        if default_figures and not isinstance(default_figures, list):
            default_figures = [default_figures]
        self.default_figures = default_figures or [go.Figure()]
        self.update_interval_id = update_interval_id
        self.data_update_function = data_update_function
        self.update_data_params = {}  # Adicionar o atributo update_data_params

        # Inicializa os títulos
        if figure_titles and not isinstance(figure_titles, list):
            figure_titles = [figure_titles]
        self.figure_titles = figure_titles or []
        self.default_title = default_title
        self.initial_cards = initial_cards

        # IDs base para componentes dinâmicos
        self.component_ids = {
            'store': f'{self.container_id}-oldSum',
            'figures_store': f'{self.container_id}-figures-store',
            'editor_menu': f'{self.container_id}-editorMenu',
            'editor': f'{self.container_id}-editor',
            'chart_id': f'{self.container_id}-chartId',
            'reset_editor': f'{self.container_id}-resetEditor',
            'save_editor': f'{self.container_id}-saveEditor',
            'save_close_editor': f'{self.container_id}-saveCloseEditor',
            'add_chart': f'{self.container_id}-add-chart',
            'dynamic_edit': f'{self.container_id}-dynamic-edit',
            'dynamic_delete': f'{self.container_id}-dynamic-delete',
            'dynamic_output': f'{self.container_id}-dynamic-output',
            'dynamic_card': f'{self.container_id}-dynamic-card',
        }

        # Cria os componentes
        self.modal = self._create_modal(modal_size)
        self.store = dcc.Store(id=self.component_ids['store'], data=0)
        self.figures_store = dcc.Store(
            id=self.component_ids['figures_store'], data=self.default_figures
        )

        # Registra as callbacks
        self._register_callbacks()

    def _create_modal(self, size):
        return dmc.Modal(
            children=[
                dmc.Group(
                    [
                        dmc.Title(
                            'Editando Gráfico com Identificador', order=3
                        ),
                        dmc.NumberInput(
                            id=self.component_ids['chart_id'],
                            variant='unstyled',
                            min=0,
                            size='xl',
                            w='5%',
                        ),
                    ],
                    justify='center',
                    mt='md',
                ),
                dce.DashChartEditor(
                    dataSources=self.data_source,
                    id=self.component_ids['editor'],
                    style={'height': '60vh'},
                ),
                dmc.Group(
                    [
                        dmc.Button(
                            'Reset', id=self.component_ids['reset_editor']
                        ),
                        dmc.Button(
                            'Save', id=self.component_ids['save_editor']
                        ),
                        dmc.Button(
                            'Save & Close',
                            id=self.component_ids['save_close_editor'],
                            variant='outline',
                        ),
                    ],
                    justify='flex-end',
                    mt='md',
                ),
            ],
            id=self.component_ids['editor_menu'],
            size=size,
            opened=False,
        )

    def make_card(self, n_clicks):
        click_number = 0 if n_clicks is None else n_clicks
        # Seleciona figura padrão e título
        fig_index = click_number % len(self.default_figures)
        default_fig = self.default_figures[fig_index]

        # Seleciona título específico se disponível, senão usa o padrão
        if fig_index < len(self.figure_titles):
            title = self.figure_titles[fig_index]
        else:
            title = f'{self.default_title} {click_number + 1}'

        return dmc.Card(
            children=[
                dmc.CardSection(
                    dmc.Group(
                        [
                            dmc.Text(
                                title,  # Usa o título selecionado
                                fw=500,
                            ),
                            dmc.Group(
                                [
                                    dmc.Button(
                                        'Editar ?',
                                        id={
                                            'type': self.component_ids[
                                                'dynamic_edit'
                                            ],
                                            'index': n_clicks,
                                        },
                                        variant='light',
                                        size='sm',
                                    ),
                                    dmc.Button(
                                        'X',
                                        id={
                                            'type': self.component_ids[
                                                'dynamic_delete'
                                            ],
                                            'index': n_clicks,
                                        },
                                        variant='subtle',
                                        color='red',
                                        size='sm',
                                    ),
                                ],
                                gap='xs',
                            ),
                        ],
                        justify='space-between',
                    ),
                    withBorder=True,
                    inheritPadding=True,
                    py='xs',
                ),
                dmc.CardSection(
                    dcc.Graph(
                        id={
                            'type': self.component_ids['dynamic_output'],
                            'index': n_clicks,
                        },
                        style={'height': 400},
                        figure=default_fig,  # Usa a figura selecionada
                    )
                ),
            ],
            withBorder=True,
            shadow='sm',
            radius='md',
            w=self.card_size,
            style={'width': 400, 'display': 'inline-block'},
            m='xs',
            id={
                'type': self.component_ids['dynamic_card'],
                'index': n_clicks,
            },
        )

    def _register_callbacks(self):
        @self.app.callback(
            Output(self.container_id, 'children'),
            Input(self.component_ids['add_chart'], 'n_clicks'),
        )
        def add_card(n_clicks):
            if n_clicks is None:
                return no_update
            patched_children = Patch()
            new_card = self.make_card(n_clicks)
            patched_children.append(new_card)
            return patched_children

        @self.app.callback(
            Output(self.container_id, 'children', allow_duplicate=True),
            Input(
                {'type': self.component_ids['dynamic_delete'], 'index': ALL},
                'n_clicks',
            ),
            State(
                {'type': self.component_ids['dynamic_card'], 'index': ALL},
                'id',
            ),
            prevent_initial_call=True,
        )
        def remove_card(_, ids):
            cards = Patch()
            trigger_value = ctx.triggered[0].get('value')
            if trigger_value is not None and trigger_value > 0:
                for i in range(len(ids)):
                    if ids[i]['index'] == ctx.triggered_id['index']:
                        del cards[i]
                        return cards
            return no_update

        @self.app.callback(
            Output(self.component_ids['editor_menu'], 'opened'),
            Output(self.component_ids['editor'], 'loadFigure'),
            Output(self.component_ids['chart_id'], 'value'),
            Output(self.component_ids['store'], 'data'),
            Input(
                {'type': self.component_ids['dynamic_edit'], 'index': ALL},
                'n_clicks',
            ),
            State(
                {'type': self.component_ids['dynamic_output'], 'index': ALL},
                'figure',
            ),
            State(self.component_ids['store'], 'data'),
            State(
                {'type': self.component_ids['dynamic_card'], 'index': ALL},
                'id',
            ),
            prevent_initial_call=True,
        )
        def edit_card(edit, figs, oldSum, ids):
            edit_sum = sum(x or 0 for x in edit)
            oldSum = min(oldSum, edit_sum)
            if edit_sum > 0 and edit_sum > oldSum:
                oldSum = edit_sum
                if ctx.triggered[0]['value'] > 0:
                    for i in range(len(ids)):
                        if ids[i]['index'] == ctx.triggered_id['index']:
                            if figs[i]['data']:
                                return (
                                    True,
                                    figs[i],
                                    ctx.triggered_id['index'],
                                    oldSum,
                                )
                            return (
                                True,
                                {'data': [], 'layout': {}},
                                ctx.triggered_id['index'],
                                oldSum,
                            )
            return no_update, no_update, no_update, oldSum

        @self.app.callback(
            Output(
                self.component_ids['editor'],
                'loadFigure',
                allow_duplicate=True,
            ),
            Input(self.component_ids['reset_editor'], 'n_clicks'),
            State(
                {'type': self.component_ids['dynamic_output'], 'index': ALL},
                'figure',
            ),
            State(self.component_ids['chart_id'], 'value'),
            State(
                {'type': self.component_ids['dynamic_card'], 'index': ALL},
                'id',
            ),
            prevent_initial_call=True,
        )
        def reset_figure(n_clicks, figs, chartId, ids):
            if n_clicks is None:
                return no_update

            for i in range(len(ids)):
                if ids[i]['index'] == chartId:
                    if figs[i].get('data'):
                        return figs[i]
            return {'data': [], 'layout': {}}

        @self.app.callback(
            Output(self.component_ids['editor'], 'saveState'),
            Input(self.component_ids['save_editor'], 'n_clicks'),
            Input(self.component_ids['save_close_editor'], 'n_clicks'),
        )
        def save_figure(n, n1):
            if n or n1:
                return True
            return no_update

        @self.app.callback(
            Output(
                self.component_ids['editor_menu'],
                'opened',
                allow_duplicate=True,
            ),
            Input(self.component_ids['save_close_editor'], 'n_clicks'),
            prevent_initial_call=True,
        )
        def close_editor(n):
            if n:
                return False
            return no_update

        # Cria um ID dinâmico específico para
        # cada instância para o componente code-highlight
        code_highlight_id = 'code-highlight'

        @self.app.callback(
            Output(self.container_id, 'children', allow_duplicate=True),
            Output(code_highlight_id, 'code', allow_duplicate=True),
            Input(self.component_ids['editor'], 'figure'),
            State(self.component_ids['chart_id'], 'value'),
            State(
                {'type': self.component_ids['dynamic_card'], 'index': ALL},
                'id',
            ),
            prevent_initial_call=True,
        )
        def save_to_card(f, v, ids):
            if f:
                figs = Patch()

                for i in range(len(ids)):
                    if ids[i]['index'] == v:
                        figs[i]['props']['children'][1]['props']['children'][
                            'props'
                        ]['figure'] = f
                        figure = dce.chartToPython(f, self.df1)
                        return figs, str(figure)
            return no_update, no_update

        # Nova callback para atualização periódica dos gráficos
        if self.update_interval_id:

            @self.app.callback(
                Output(self.component_ids['figures_store'], 'data'),
                Output(
                    {
                        'type': self.component_ids['dynamic_output'],
                        'index': ALL,
                    },
                    'figure',
                    allow_duplicate=True,
                ),
                Output(
                    self.component_ids['editor'],
                    'dataSources',
                    allow_duplicate=True,
                ),
                Input(self.update_interval_id, 'n_intervals'),
                State(
                    {
                        'type': self.component_ids['dynamic_card'],
                        'index': ALL,
                    },
                    'id',
                ),
                prevent_initial_call=True,
            )
            def update_data_periodically(n_intervals, ids):
                if n_intervals is None or self.data_update_function is None:
                    return no_update, no_update, no_update

                # Obter dados atualizados usando os parâmetros de data
                updated_data_source, updated_figures = (
                    self.data_update_function(**self.update_data_params)
                )

                if updated_data_source is not None:
                    self.df1 = updated_data_source
                    self.data_source = updated_data_source.to_dict('list')

                if updated_figures is not None:
                    self.default_figures = updated_figures

                    # Atualizar todos os gráficos existentes
                    updated_graphs = []
                    for i in range(len(ids)):
                        fig_index = ids[i]['index'] % len(updated_figures)
                        updated_graphs.append(updated_figures[fig_index])

                    return updated_figures, updated_graphs, self.data_source

                return no_update, no_update, no_update

    def get_layout(self):
        # Criar cards iniciais
        initial_children = (
            [self.make_card(i) for i in range(self.initial_cards)]
            if self.initial_cards > 0
            else []
        )

        # Cria o componente code-highlight específico para essa instância
        code_highlight = dcc.Store(
            id=f'{self.instance_id}-code-highlight', data=''
        )

        return dmc.Container(
            [
                self.store,
                self.figures_store,  # Nova store para armazenar figuras
                code_highlight,  # Adiciona o componente code-highlight
                dmc.Button(
                    'Adicionar Novo Gráfico?',
                    id=self.component_ids['add_chart'],
                    variant='filled',
                    n_clicks=self.initial_cards,
                ),
                dmc.Group(
                    id=self.container_id,
                    children=initial_children,
                    className='mt-4',
                ),
                self.modal,
            ],
            fluid=True,
            px=0,
            py=0,
        )


if __name__ == '__main__':
    import plotly.express as px
    from dash import _dash_renderer  # noqa: PLC2701

    _dash_renderer._set_react_version('18.2.0')

    app = Dash(__name__)

    # Criar múltiplas figuras padrão de exemplo
    df = px.data.iris()
    default_figs = [
        px.scatter(df, x='sepal_length', y='sepal_width', color='species'),
        px.box(df, x='species', y='petal_length'),
        px.histogram(df, x='sepal_width', color='species'),
    ]

    # Definir títulos específicos para cada figura
    figure_titles = [
        'Scatter Plot - Sepal Length vs Width',
        'Box Plot - Petal Length by Species',
        'Histogram - Sepal Width Distribution',
    ]

    # Exemplo de uso com duas instâncias diferentes
    editor1 = ChartEditor(
        app,
        instance_id='page1',  # ID de instância único para primeira página
        data_source=df,
        default_figures=default_figs[:2],  # Primeiros dois gráficos
        figure_titles=figure_titles[:2],
        default_title='Iris Chart Page 1',
        card_size=400,
        initial_cards=2,
    )

    editor2 = ChartEditor(
        app,
        instance_id='page2',  # ID de instância único para segunda página
        data_source=df,
        default_figures=default_figs[1:],  # A partir do segundo gráfico
        figure_titles=figure_titles[1:],
        default_title='Iris Chart Page 2',
        card_size=400,
        initial_cards=2,
    )

    # Layout da aplicação com as duas instâncias em abas diferentes
    app.layout = dmc.MantineProvider(
        [
            dmc.Tabs(
                [
                    dmc.TabsList([
                        dmc.Tab('Página 1', value='page1'),
                        dmc.Tab('Página 2', value='page2'),
                    ]),
                    dmc.TabsPanel(editor1.get_layout(), value='page1'),
                    dmc.TabsPanel(editor2.get_layout(), value='page2'),
                ],
                value='page1',
                id='page-tabs',
            ),
        ],
        id='mantine-provider',
        forceColorScheme='light',
    )

    app.run(debug=True, port=1234)
