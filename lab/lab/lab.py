import reflex as rx
import tzfpy


class State(rx.State):
    tz: str = ""

    def get_tz(self, form_data):
        lng = float(form_data["lng"])
        lat = float(form_data["lat"])
        name = tzfpy.get_tz(lng, lat)
        self.tz = name


def index() -> rx.Component:
    return rx.container(
        rx.form(
            rx.color_mode.button(position="top-right"),
            rx.heading("Timezone Lookup", size="9"),
            rx.text("Enter a latitude and longitude to find the timezone.", size="5"),
            rx.input("Longitude", placeholder="Enter longitude", name="lng", value=-74.0060),
            rx.input("Latitude", placeholder="Enter latitude", name="lat", value=40.7128),
            rx.text("Timezone: ", size="5"),
            rx.text(State.tz, size="5", color="blue.500"),  # Display timezone result here
            rx.button("Submit", type="submit"),
            on_submit=State.get_tz,
        ),
    )


app = rx.App()
app.add_page(index)
