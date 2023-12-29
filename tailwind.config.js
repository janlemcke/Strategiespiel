module.exports = {
    content: [
        "./account/**/*.{html,js}",
        "./building/**/*.{html,js}",
        "./core/**/*.{html,js}",],
    theme: {
        extend: {},
    },
    plugins: [require("daisyui")],
    daisyui: {
        themes: ["emerald"],
    },
}