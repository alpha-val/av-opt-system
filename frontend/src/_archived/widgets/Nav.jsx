import { AppBar, Toolbar, Box } from "@mui/material";
import React from "react";
import logo from "../media/images/logo.png";

const Nav = () => {
    return (
        <AppBar position="static" sx={{ backgroundColor: 'primary.main', color: '#fff', height: '64px', p: 0 }}>
            <Toolbar>
                <Box
                    component="a"
                    href="/"
                    sx={{
                        display: "flex",
                        alignItems: "center",
                        textDecoration: "none",
                        height: 80,

                    }}
                >
                    <Box
                        component="img"
                        src={logo}
                        alt="OptPro Logo"
                        sx={{
                            backgroundColor: "white",
                            height: 80,
                            width: "auto",
                            display: "block",
                        }}
                    />
                </Box>
            </Toolbar>
        </AppBar>
    );
};

export default Nav;