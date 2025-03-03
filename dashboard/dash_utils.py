import plotly.graph_objects as go


def add_delta_trace(fig, title, value, last_value, row, column):  # noqa: PLR0913, PLR0917
    fig.add_trace(
        go.Indicator(
            mode='number+delta',
            title={'text': title},
            value=value,
            delta={'reference': last_value, 'relative': True},
            domain={'row': row, 'column': column},
            # definindo a quantidade de digitos após a virgula
            number={'valueformat': '.2f'},
        )
    )


# funcão para criar um indicador de semi-circulo
def add_gauge_trace(fig, title, value, gauge, row, column):  # noqa: PLR0913, PLR0917
    fig.add_trace(
        go.Indicator(
            mode='gauge+number',
            title={'text': title},
            value=value,
            gauge=gauge,
            domain={'row': row, 'column': column},
        )
    )


def add_trace(fig, title, value, row, column):
    fig.add_trace(
        go.Indicator(
            mode='number',
            title={'text': title},
            value=value,
            domain={'row': row, 'column': column},
            # definindo a quantidade de digitos após a virgula
            number={'valueformat': '.2f'},
        )
    )
